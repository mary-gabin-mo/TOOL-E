import cv2
import platform
import os
import time
import threading
import numpy as np
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.graphics.texture import Texture
from View.baseScreen import BaseScreen
from PIL import Image, ImageOps

# Detect if we are on the Pi
IS_RASPBERRY_PI = platform.machine() in ("aarch64", "armv7l")

class CaptureScreen(BaseScreen):
    
    capture = None  # For OpenCV (laptop)
    picam2 = None   # For Picamera2 (Pi)
    update_event = None
    
    def on_enter(self):
        """
        Called when this screen is displayed.
        Starts listeining to hardware events here.
        """
        print(f"[DEBUG] CaptureScreen: on_enter called.")
        
        # 1. Reset UI to "Initializing" State
        self.set_processing_mode(True, message="Initializing Camera...")
        
        # 2. Bind hardware Events
        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            app.hardware.bind(on_load_cell_detect=self.handle_load_cell_trigger)
            
        # 3. Start Camera in Background (So UI doesn't freeze)
        threading.Thread(target=self._init_camera_async).start()
        
    def _init_camera_async(self):
        """background init to prevent UI freeze"""
        print(f"[UI] Initializing Camera (Pi Mode: {IS_RASPBERRY_PI})...")
        success = False
        try:
            if IS_RASPBERRY_PI:
                from picamera2 import Picamera2
                self.picam2 = Picamera2()
                
                # Configure: 'main' for high-res capture, 'lores' for the UI preview
                config = self.picam2.create_still_configuration(
                    main={"size": (1920, 1080), "format": "RGB888"},
                    lores={"size": (640, 480), "format": "RGB888"},
                )
                self.picam2.configure(config)
                self.picam2.start()
                success = True
            else:
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
        if success:
            # Turn off spinner, show camera
            self.set_processing_mode(False)
            self.update_event = Clock.schedule_interval(self.update_feed, 1.0/30.0)
            
        else:
            self.ids.loading_label.text = "Camera Error!"
    
    def on_leave(self):
        """
        Called when leaving this screen.
        Stop listening so this logic doesn't get triggered on other screens.
        """
        app = App.get_running_app()
        
        # 1. Unbind Hardware
        if hasattr(app, 'hardware'):
            app.hardware.unbind(on_load_cell_detect=self.handle_load_cell_trigger)
            
        # 2. Stop Update Loop
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None
            
        # 3. Stop Pi Camera
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
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
            self.ids.loading_spinner.active = True
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
            self.ids.loading_spinner.active = False
            self.ids.camera_preview.opacity = 1
            
    def update_feed(self, dt):
        """
        Reads a frame from OpenCV and updates the Kivy Image widget.
        """
        frame = None
        # 1. Get the frame (as numpy array)
        if IS_RASPBERRY_PI and self.picam2:
            # Capture from the law-res stream for speed
            try: 
                frame = self.picam2.capture_array("lores")
            except Exception:
                pass
        elif self.capture:
            ret, cv_frame = self.capture.read()
            if ret:
                # OpenCV is BGR - convert it RGB for Kivy
                frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
                
        # 2. Process frame into Texture
        if frame is not None:
            # Flip vertical (Kivy standard)
            frame = cv2.flip(frame, 0)
            
            # Create texture
            # Note: Frame.shape is (height, width, colors)
            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]),
                colorfmt='rgb'
            )
            # Convert to bytes
            texture.blit_buffer(frame.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
            if self.ids.get('camera_preview'):
                self.ids.camera_preview.texture = texture
            
    def handle_load_cell_trigger(self, instance, weight):
        """
        Logic for when the load cell is triggered.
        """
        print(f"[UI] Capture Screen detected load cell trigger: {weight}")
        
        # 1. Update UI to "Processing" state immeidately
        self.set_processing_mode(True, message="Analyzing Image...")
        
        # 2. Capture Image
        filepath = self.save_current_frame()
        
        if filepath:
            # 3. Start API upload in background
            print(f"[DEBUG] Image saved successfully at {filepath}. Starting API thread...")
            threading.Thread(target=self.run_identification_task, args=(filepath,)).start()
        else:
            print("[DEBUG] Failed to save image. Aborting API call.")
            self.set_processing_mode(False) # Reset if save failed
            self.update_event = Clock.schedule_interval(self.update_feed, 1.0, 30.0) # Restart camera
    
    # --- DEV - CAPTURE WITH BUTTON - REMOVE LATER --- 
    def capture_btn(self, weight):
        """Dev Button Wrapper"""
        self.handle_load_cell_trigger(None, weight)
    
    def save_current_frame(self):
        """
        Save high-res photo and resize using the PIL logic
        """
        # 1. Generate Transaction ID (Timestamp)
        # Format: YYYYMMDD_HHMMSS(e.g., 20260202_183005)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(datetime.now().microsecond / 1000)
        timestamp_id = f"{timestamp}-{milliseconds:03d}"
        # 2. Create Filename
        filename = f"{timestamp_id}.jpg"        
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
                print (f"[UI] Image saved: {filename}")
                
                # 3. Update Session
                app = App.get_running_app()
                if hasattr(app, 'session'):
                    # Start the transaction now with ID and filename
                    app.session.start_new_transaction(
                        transaction_id=timestamp_id,
                        img_filename=full_path
                    )
                return full_path
                
        except Exception as e:
            print(f"[UI] Save Error: {e}")
            return None
            
    def process_image_pil(self, filepath):
        """
        Custom resizing logic using PIl
        """
        try:
            target_size = 384
            img = Image.open(filepath)
            
            # Pad and Resize
            new_img = ImageOps.pad(
                img,
                (target_size, target_size),
                method=image.LANCZOS,
                color="white",
                centering=(0.5, 0.5),
            )
            
            new_img.save(filepath, quality=95)
            print(f"[UI] Image resized/padded to {target_size}x{target_size}")
            
        except Exception as e:
            print(f"[UI] PIL Error: {e}")

    def run_identification_task(self, filepath):
        """Background Thread: uploads image to server."""
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
        print(f"[UI] Identification Result: {result}")
        
        if result and result.get('success'):
            app = App.get_running_app()
            if hasattr(app, 'session'):
                # Extract the nested dictionary from 'data'
                # API returns: {'success': True, 'data: {'prediction': '...', ...}}
                tool_data = result.get('data', {})
                app.session.identified_tool_data = tool_data
                print(f"[DEBUG] Saved tool info to session: {tool_data}")
                
            # Navigate to Confirmation
            self.go_to('tool confirm screen')
        else:
            # Handle Error (e.g. show error screen or text)
            error_msg = result.get('error', 'Unknown Error') if result else "Connection Failed"
            print(f"[UI Error] {error_msg}")
            
    def reset_feed(self):
        self.set_processing_mode(False) # hide spinner
        self.update_event = Clock.schedule_interval(self.update_feed, 1.0/30.0)
