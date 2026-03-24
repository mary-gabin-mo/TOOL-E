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

# Keep camera init work separate from capture/upload work.
_camera_init_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CaptureInit-")
_capture_work_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="CaptureWork-")


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
        Starts listening to hardware events.
        """
        print("[DEBUG] CaptureScreen: on_enter called.")
        self._screen_active = True
        self._is_capturing = False

        if self._pending_capture_event:
            self._pending_capture_event.cancel()
            self._pending_capture_event = None

        # Reset UI while camera initializes
        self.set_processing_mode(True, message="Initializing Camera...")

        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            print("[DEBUG] Hardware manager found. Binding to on_load_cell_detect...")
            app.hardware.bind(on_load_cell_detect=self.handle_load_cell_trigger)
            print("[DEBUG] Successfully bound to on_load_cell_detect event")
        else:
            print("[ERROR] Hardware manager not found in app!")

        if self._is_initializing:
            print("[DEBUG] Camera init already in progress; skipping duplicate init.")
            return

        self._is_initializing = True
        _camera_init_pool.submit(self._init_camera_async)

    def _init_camera_async(self):
        """Background camera init to prevent UI freeze."""
        print(f"[UI] Initializing Camera (Pi Mode: {IS_RASPBERRY_PI})...")
        success = False

        try:
            if IS_RASPBERRY_PI:
                if self.picam2 is None:
                    from picamera2 import Picamera2
                    self.picam2 = Picamera2()
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
                success = bool(self.capture and self.capture.isOpened())
        except Exception as e:
            print(f"[UI] CRITICAL camera init error: {e}")

        self._on_camera_ready(success)

    @mainthread
    def _on_camera_ready(self, success):
        self._is_initializing = False

        # Ignore stale init completion after navigation away.
        if not self._screen_active:
            if success:
                self._close_camera_resources()
            return

        if success:
            self.set_processing_mode(False)
            self._start_feed()
        else:
            self.ids.loading_label.text = "Camera Error!"

    def _start_feed(self):
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None
        update_interval = 1.0 / 15.0 if IS_RASPBERRY_PI else 1.0 / 30.0
        self.update_event = Clock.schedule_interval(self.update_feed, update_interval)

    def on_leave(self):
        """
        Called when leaving this screen.
        """
        self._screen_active = False
        self._is_initializing = False
        self._is_capturing = False

        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            app.hardware.unbind(on_load_cell_detect=self.handle_load_cell_trigger)

        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

        if self._pending_capture_event:
            self._pending_capture_event.cancel()
            self._pending_capture_event = None

        self._close_camera_resources()

    def _close_camera_resources(self):
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

        if self.capture:
            self.capture.release()
            self.capture = None
            print("[UI] Webcam released.")

    @mainthread
    def set_processing_mode(self, is_processing, message="Processing..."):
        if is_processing:
            self.ids.processing_overlay.opacity = 1
            self.ids.loading_label.text = message
            self.ids.camera_preview.opacity = 0.3
            if self.update_event:
                self.update_event.cancel()
                self.update_event = None
        else:
            self.ids.processing_overlay.opacity = 0
            self.ids.camera_preview.opacity = 1

    def update_feed(self, dt):
        frame = None

        if IS_RASPBERRY_PI and self.picam2:
            try:
                frame = self.picam2.capture_array("lores")
            except Exception:
                pass
        elif self.capture:
            ret, cv_frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)

        if frame is None:
            return

        if not IS_RASPBERRY_PI:
            frame = cv2.flip(frame, 0)

        if not self.ids.get('camera_preview'):
            return

        expected_size = (frame.shape[1], frame.shape[0])
        texture = self.ids.camera_preview.texture
        if not texture or texture.size != expected_size:
            texture = Texture.create(size=expected_size, colorfmt='rgb')
            self.ids.camera_preview.texture = texture

        try:
            texture.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        except Exception:
            pass

    def handle_load_cell_trigger(self, instance, weight):
        """
        Triggered by hardware when object is detected on load cell.
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

        print("[DEBUG] Waiting 1.5 seconds for object to settle...")
        self._pending_capture_event = Clock.schedule_once(self._delayed_capture, 1.5)

    def _delayed_capture(self, dt):
        self._pending_capture_event = None

        if not self._screen_active or self._is_capturing:
            return

        self._is_capturing = True
        print("[DEBUG] Freezing camera and capturing image...")
        self.set_processing_mode(True, message="Capturing Image...")

        _capture_work_pool.submit(self.run_identification_task)

    # --- DEV - CAPTURE WITH BUTTON - REMOVE LATER ---
    def capture_btn(self, *args):
        print("[DEV] Manual capture button pressed")
        self.handle_load_cell_trigger(None, 100.0)

    def save_current_frame(self):
        """
        Save high-res photo and resize using PIL logic.
        """
        print("[DEBUG] save_current_frame() called")
        print(f"[DEBUG] IS_RASPBERRY_PI: {IS_RASPBERRY_PI}")
        print(f"[DEBUG] self.picam2: {self.picam2}")
        print(f"[DEBUG] self.capture: {self.capture}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(datetime.now().microsecond / 1000)
        timestamp_id = f"{timestamp}-{milliseconds:03d}"

        app = App.get_running_app()
        tx_type = "BORROW"
        if hasattr(app, 'session') and getattr(app.session, 'transaction_type', None):
            tx_type = app.session.transaction_type.upper()

        filename = f"{timestamp_id}_{tx_type}.jpg"
        full_path = os.path.abspath(filename)

        success = False
        try:
            if IS_RASPBERRY_PI and self.picam2:
                self.picam2.capture_file(filename)
                print(f"[UI] Raw Pi image saved to {filename}")
                self.process_image_pil(filename)
                success = True
            elif self.capture:
                ret, frame = self.capture.read()
                if ret:
                    cv2.imwrite(filename, frame)
                    self.process_image_pil(filename)
                    success = True

            if success:
                print(f"[UI] Image saved locally: {filename}")
                if hasattr(app, 'session'):
                    app.session.start_new_transaction(
                        transaction_id=timestamp_id,
                        img_filename=full_path,
                    )
                return full_path

        except Exception as e:
            print(f"[UI] Save Error: {e}")

        return None

    def process_image_pil(self, filepath):
        """
        Resize captured image for ML model input.
        """
        try:
            target_size = 384
            img = Image.open(filepath)
            new_img = ImageOps.pad(
                img,
                (target_size, target_size),
                method=Image.BILINEAR,
                color="white",
                centering=(0.5, 0.5),
            )
            new_img.save(filepath, quality=85, optimize=True)
            print(f"[UI] Image resized/padded to {target_size}x{target_size} with optimized quality")
        except Exception as e:
            print(f"[UI] PIL Error: {e}")

    def run_identification_task(self):
        """Background task: capture, preprocess, upload to server."""
        filepath = self.save_current_frame()

        if not filepath:
            print("[ERROR] Failed to save image. Aborting API call.")
            self.handle_identification_result({'success': False, 'error': 'Failed to save image'})
            return

        print(f"[Background] Uploading {filepath}...")
        app = App.get_running_app()

        try:
            result = app.api_client.upload_tool_image(filepath)
        except Exception as e:
            result = {'success': False, 'error': str(e)}

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
                tool_data = result.get('data', {})
                app.session.identified_tool_data = tool_data
                print(f"[DEBUG] Saved tool info to session: {tool_data}")

            prediction = tool_data.get('prediction', 'UNKNOWN')
            score = tool_data.get('score', 0)
            is_return_flow = hasattr(app, 'session') and app.session.transaction_type == "return"

            if str(prediction).upper() == 'UNKNOWN' or float(score) < 0.60:
                print(f"[UI] Low confidence ({score}) or UNKNOWN ({prediction}). Bypassing confirm screen.")
                if is_return_flow:
                    app.session.tool_was_confirmed = False
                    app.session.set_classification_correct(False)
                    self.go_to('tool return selection screen')
                else:
                    self.go_to('tool select screen')
            else:
                self.go_to('tool confirm screen')
        else:
            error_msg = result.get('error', 'Unknown Error') if result else 'Connection Failed'
            print(f"[UI Error] {error_msg}")
            self.reset_feed()

    def reset_feed(self):
        self._is_capturing = False
        self.set_processing_mode(False)
        self._start_feed()
