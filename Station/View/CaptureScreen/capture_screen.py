import cv2
import platform
import os
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.graphics.texture import Texture
from View.baseScreen import BaseScreen
from PIL import Image, ImageOps

# Suppress debug logging from picamera2 and other libraries
logging.getLogger('picamera2').setLevel(logging.WARNING)
logging.getLogger('libcamera').setLevel(logging.WARNING)
logging.getLogger('picamera2.job').setLevel(logging.WARNING)

# Detect if we are on the Pi
IS_RASPBERRY_PI = platform.machine() in ("aarch64", "armv7l")

# Separate pools keep camera startup responsive even while identification is running.
_camera_init_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CaptureScreen-Init-")
_identify_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="CaptureScreen-Identify-")

class CaptureScreen(BaseScreen):
    
    capture = None  # For OpenCV (laptop)
    picam2 = None   # For Picamera2 (Pi)
    update_event = None
    _pending_capture_event = None
    _is_initializing = False
    _is_capturing = False
    _screen_active = False
    
    def on_enter(self):
        """
        Called when this screen is displayed.
        Starts listeining to hardware events here.
        """
        print(f"[DEBUG] CaptureScreen: on_enter called.")
        self._screen_active = True
        self._is_capturing = False
        
_camera_init_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CaptureInit-")
_capture_work_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="CaptureWork-")
        
        # 2. Bind hardware Events
        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            print("[DEBUG] Hardware manager found. Binding to on_load_cell_detect...")
            app.hardware.bind(on_load_cell_detect=self.handle_load_cell_trigger)
    _pending_capture_event = None
    _is_initializing = False
    _is_capturing = False
    _screen_active = False
            print("[DEBUG] Successfully bound to on_load_cell_detect event")
        else:
            print("[ERROR] Hardware manager not found in app!")
            
        # 3. Start camera in background unless already initializing.
        if self._is_initializing:
            print("[DEBUG] Camera init already in progress; skipping duplicate on_enter init.")
            return

        self._is_initializing = True
        _camera_init_pool.submit(self._init_camera_async)
        
    def _init_camera_async(self):
        """Background init to prevent UI freeze (run in thread pool)"""
        print(f"[UI] Initializing Camera (Pi Mode: {IS_RASPBERRY_PI})...")
        success = False
        try:
            if IS_RASPBERRY_PI:
                if self.picam2 is None:
                    from picamera2 import Picamera2
                    self.picam2 = Picamera2()
                    
                    # OPTIMIZATION: Optimized resolution for Pi - process at lower res
                    config = self.picam2.create_still_configuration(
                        main={"size": (1280, 720), "format": "RGB888"},
                        lores={"size": (480, 360), "format": "RGB888"},
                    )
                    self.picam2.configure(config)
                    self.picam2.start()
                success = True
            else:
                if self.capture is None:
                    self.capture = cv2.VideoCapture(0)
                if self.capture.isOpened():
                    success = True
        except Exception as e:
            print(f"[UI] CRITICAL Picamera2 Error: {e}.")
        
        # Report back to Main Thread
        self._on_camera_ready(success)
        
    @mainthread
    def _on_camera_ready(self, success):
        """Called on Main Thread after initializing"""
        self._is_initializing = False

        # If we already navigated away, do not start preview updates.
        if not self._screen_active:
            if success:
                self._close_camera_resources()
            return

        if success:
            # Turn off spinner, show camera
            self.set_processing_mode(False)
            # OPTIMIZATION: Reduce frame rate from 30fps to 15fps for Pi
            # This cuts CPU usage significantly while maintaining smooth visuals
            update_interval = 1.0 / 15.0 if IS_RASPBERRY_PI else 1.0 / 30.0
            if self.update_event is None:
                self.update_event = Clock.schedule_interval(self.update_feed, update_interval)
            
        else:
            self.ids.loading_label.text = "Camera Error!"
    
    def on_leave(self):
        """
        Called when leaving this screen.
        Stop listening so this logic doesn't get triggered on other screens.
        """
        self._screen_active = False
        self._is_initializing = False
        self._is_capturing = False

        app = App.get_running_app()
        
        # 1. Unbind Hardware
        if hasattr(app, 'hardware'):
            app.hardware.unbind(on_load_cell_detect=self.handle_load_cell_trigger)
            
        # 2. Stop Update Loop
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

        # Cancel delayed capture callback if it has not run yet.
        if self._pending_capture_event:
            self._pending_capture_event.cancel()
            self._pending_capture_event = None
            
        # 3. Release camera resources.
        self._close_camera_resources()

    def _close_camera_resources(self):
        # Stop Pi Camera
        if self.picam2:
            try:
                self.picam2.stop()
            except Exception:
                pass
            try:
                self.picam2.close()
            except Exception:
                pass
            self.picam2 = None
            print("[UI] Picamera2 closed.")

        # Stop Laptop Camera
        if self.capture:
            self.capture.release()
            self.capture = None
            print("[UI] WebCame released.")

    @mainthread
    def set_processing_mode(self, is_processing, message="Processing..."):
        """
        Toggles the UI between 'Live Feed' and 'Loading Spinner'.
        """
        if is_processing:
            # Show Spinner Overlay
            self.ids.processing_overlay.opacity = 1
            self.ids.loading_label.text = message
            
            # Dim the camera feed slightly to focus on spinner
            self.ids.camera_preview.opacity = 0.3
            
            # Stop the feed update to save CPU while processing
            if self.update_event:
                self.update_event.cancel()
                self.update_event = None
            
        else:
            # Show live feed
            self.ids.processing_overlay.opacity = 0
            self.ids.camera_preview.opacity = 1
            
    def update_feed(self, dt):
        """
        Reads a frame from OpenCV and updates the Kivy Image widget.
        OPTIMIZATION: Simplified frame processing and texture management.
        """
        frame = None
        # 1. Get the frame (as numpy array)
        if IS_RASPBERRY_PI and self.picam2:
            # Capture from the low-res stream for speed
            try: 
                frame = self.picam2.capture_array("lores")
            except Exception:
                pass
        elif self.capture:
            ret, cv_frame = self.capture.read()
            if ret:
                # OpenCV is BGR - convert it RGB for Kivy
                frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
                
        # 2. Process frame into Texture (OPTIMIZED)
        if frame is not None:
            # Skip expensive flip operation if not necessary on Pi
            if not IS_RASPBERRY_PI:
                frame = cv2.flip(frame, 0)
            
            if self.ids.get('camera_preview'):
                expected_size = (frame.shape[1], frame.shape[0])
                texture = self.ids.camera_preview.texture
                
                # OPTIMIZATION: Only create texture once, reuse and update
                # Skip recreation if size matches to avoid GPU overhead
                if not texture or texture.size != expected_size:
                    texture = Texture.create(size=expected_size, colorfmt='rgb')
                    self.ids.camera_preview.texture = texture
                else:
                    # Reuse existing texture - much faster
                    pass
                
                # OPTIMIZATION: Use bgr format directly to avoid extra conversion
                # Also batch the buffer update with canvas update
                try:
                    texture.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                except:
                    # If blit fails (e.g., frame size mismatch), skip this frame
                    pass
            
    def handle_load_cell_trigger(self, instance, weight):
        """
        Logic for when the load cell is triggered.
        Delays capture by 1.5 seconds to let object settle.
        Camera stays LIVE during the delay, then freezes when capture happens.
        """
        if not self._screen_active or self._is_initializing:
            return

        if self._is_capturing or self._pending_capture_event is not None:
            print("[DEBUG] Capture already in progress; ignoring extra load-cell trigger.")
            return

        print(f"\n{'='*60}")
        print(f"[LOADCELL DETECTED] Raw Weight Value: {weight}")
        print(f"[LOADCELL DETECTED] Instance: {instance}")
        print(f"{'='*60}\n")
        
        # 1. Show message but keep camera LIVE (don't freeze yet)
        print("[DEBUG] Waiting 1.5 seconds for object to settle...")
        print("[DEBUG] Camera remains LIVE during delay...")
        
        # 2. Delay capture by 1.5 seconds to let object settle
        print("[DEBUG] Scheduling capture in 1.5 seconds...")
        self._pending_capture_event = Clock.schedule_once(self._delayed_capture, 1.5)
    
    def _delayed_capture(self, dt):
        """
        Called 1.5 seconds after load cell trigger.
        NOW freezes the camera and performs the actual image capture.
        """
        self._pending_capture_event = None

        if not self._screen_active or self._is_capturing:
            return

        self._is_capturing = True

        # NOW freeze the camera (right before capturing)
        print("[DEBUG] Freezing camera and capturing image...")
        self.set_processing_mode(True, message="Capturing Image...")
        
        self._pending_capture_event = Clock.schedule_once(self._delayed_capture, 1.5)
        _identify_pool.submit(self.run_identification_task)
    
    # --- DEV - CAPTURE WITH BUTTON - REMOVE LATER --- 
    def capture_btn(self, *args):
        """Dev Button: Simulate load cell trigger"""
        print("[DEV] Manual capture button pressed")
        self.handle_load_cell_trigger(None, 100.0)  # Simulate weight value
    
    def save_current_frame(self):
        """
        Save high-res photo and resize using the PIL logic
        """
        print("[DEBUG] save_current_frame() called")
        print(f"[DEBUG] IS_RASPBERRY_PI: {IS_RASPBERRY_PI}")
        print(f"[DEBUG] self.picam2: {self.picam2}")
        print(f"[DEBUG] self.capture: {self.capture}")
        
        # 1. Generate Transaction ID (Timestamp)
        _capture_work_pool.submit(self.run_identification_task)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(datetime.now().microsecond / 1000)
        timestamp_id = f"{timestamp}-{milliseconds:03d}"

        # 2. Create temp filename from tx_id + action type (BORROW/RETURN)
        app = App.get_running_app()
        tx_type = "BORROW"
        if hasattr(app, 'session') and getattr(app.session, 'transaction_type', None):
            tx_type = app.session.transaction_type.upper()
        filename = f"{timestamp_id}_{tx_type}.jpg"
        full_path = os.path.abspath(filename)
        
        success = False
        
        try:
            if IS_RASPBERRY_PI and self.picam2:
                # Capture High Res from 'main' stream
                self.picam2.capture_file(filename)
                print(f"[UI] Raw Pi image saved to {filename}")
                self.process_image_pil(filename)
                success = True
                
            elif self.capture:
                # Laptop Capture
                ret, frame = self.capture.read()
                if ret:
                    cv2.imwrite(filename, frame)
                    self.process_image_pil(filename)
                    success = True
                    
            if success:
                print (f"[UI] Image saved locally: {filename}")
                
                # 3. Update Session with local path
                if hasattr(app, 'session'):
                    # Start the transaction now with ID and local full path
                    app.session.start_new_transaction(
                        transaction_id=timestamp_id,
                        img_filename=full_path  # We temporarily store the local path here so the Kivy UI can render it
                    )
                return full_path
                
        except Exception as e:
            print(f"[UI] Save Error: {e}")
            return None
            
    def process_image_pil(self, filepath):
        """
        Custom resizing logic using PIL - OPTIMIZED for Pi performance
        """
        try:
            target_size = 384
            img = Image.open(filepath)
            
            # OPTIMIZATION: Use faster resize method (BILINEAR instead of LANCZOS)
            # BILINEAR is much faster and sufficient for ML model input
            # Also reduce quality to 85 to speed up I/O
            new_img = ImageOps.pad(
                img,
                (target_size, target_size),
                method=Image.BILINEAR,  # Changed from LANCZOS (expensive)
                color="white",
                centering=(0.5, 0.5),
            )
            
            new_img.save(filepath, quality=85, optimize=True)
            print(f"[UI] Image resized/padded to {target_size}x{target_size} with optimized quality")
            
        except Exception as e:
            print(f"[UI] PIL Error: {e}")

    def run_identification_task(self):
        """Background Thread: Takes photo, resizes, and uploads image to server."""
        # Save image and run heavy PIL resizing outside the main thread
        filepath = self.save_current_frame()

        if not filepath:
            print("[ERROR] Failed to save image. Aborting API call.")
            # Pass error back to Main UI Thread
            self.handle_identification_result({'success': False, 'error': 'Failed to save image'})
            return

        print(f"[Background] Uploading {filepath}...")
        app = App.get_running_app()
        
        # Call the API Client
        # Assumes app.api_client.upload_tool_image returns {'success': ..., 'data': ...}
        try:
            result = app.api_client.upload_tool_image(filepath)
        except Exception as e:
            result = {'success': False, 'error': str(e)}
        
        # Pass result back to Main UI Thread
        self.handle_identification_result(result)
        
    @mainthread
    def handle_identification_result(self, result):
        """
        Main Thread: Handle API response and navigate.
        """
        self._is_capturing = False
        print(f"[UI] Identification Result: {result}")
        
        if result and result.get('success'):
            app = App.get_running_app()
            tool_data = {}
            if hasattr(app, 'session'):
                # Extract the nested dictionary from 'data'
                # API returns: {'success': True, 'data': {'prediction': '...', ...}}
                tool_data = result.get('data', {})
                app.session.identified_tool_data = tool_data
                    
                print(f"[DEBUG] Saved tool info to session: {tool_data}")
                
            prediction = tool_data.get('prediction', 'UNKNOWN')
            score = tool_data.get('score', 0)
            is_return_flow = hasattr(app, 'session') and app.session.transaction_type == "return"
            
            if str(prediction).upper() == 'UNKNOWN' or float(score) < 0.60:
                print(f"[UI] Low confidence ({score}) or UNKNOWN ({prediction}). Bypassing confirm screen.")
                if is_return_flow:
                    # Return transactions must stay on return-specific path.
                    app.session.tool_was_confirmed = False
                    app.session.set_classification_correct(False)
                    self.go_to('tool return selection screen')
                else:
                    self.go_to('tool select screen')
            else:
                # Navigate to Confirmation
                self.go_to('tool confirm screen')
        else:
            # Handle Error (e.g. show error screen or text)
            error_msg = result.get('error', 'Unknown Error') if result else "Connection Failed"
            print(f"[UI Error] {error_msg}")
            # Reset UI and Restart Camera
            self.reset_feed()
            # Optionally show popup with error msg
            
    def reset_feed(self):
        self.set_processing_mode(False) # hide spinner
        update_interval = 1.0 / 15.0 if IS_RASPBERRY_PI else 1.0 / 30.0
        if self.update_event is None:
            self.update_event = Clock.schedule_interval(self.update_feed, update_interval)
