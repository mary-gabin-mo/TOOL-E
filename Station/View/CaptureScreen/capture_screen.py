import cv2
import platform
import os
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from View.baseScreen import BaseScreen

# Detect if we are on the Pi
IS_RASPBERRY_PI = platform.machine() in ("aarch64", "armv7l")

class CaptureScreen(BaseScreen):
    
    capture = None
    update_event = None
    
    def on_enter(self):
        """
        Called when this screen is displayed.
        Starts listeining to hardware events here.
        """
        app = App.get_running_app()
        
        # 1. Bind hardware Events
        if hasattr(app, 'hardware'):
            app.hardware.bind(on_load_cell_detect=self.handle_load_cell_trigger)
            
        # 2. Initialize Camera
        if IS_RASPBERRY_PI:
            try:
                # Option A: standard index 0 (works on many Pi setups if legacy camera support is enabled)
                self.capture = cv2.VideoCapture(0)

                # Check if it actually opened
                if not self.capture.isOpened():
                    print("[UI] Standard index 0 failed. Attempting GStreamer pipeline for libcamera...")
                    
                # Option B: Pi 5 / libcamera GStreamer Pipeline
                # tells OpenCV to use the GStreamer backend to talk to libcamerasrc directly
                    pipeline = (
                        "libcamerasrc ! "
                        "video/x-raw, width=640, height=480, framerate=30/1 ! "
                        "videoconvert ! "
                        "appsink"
                    )
                    self.capture = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            
            except Exception as e:
                print(f"[UI] CRITICAL Error initializing Pi Camera: {e}")
        else:
            # On Mac/Windows/Linux Desktop -> Use Laptop Webcam
            print(f"[UI] Running on Desktop/Laptop. Initializing default Webcam for testing...")
            # Index 0 is usually the built-in webcam
            self.capture = cv2.VideoCapture(0)
            
        # 3. Start the Update Loop (30 FPS)
        if self.capture and self.capture.isOpened():
            print("[UI] Camera opened successfully.")
            self.update_event = Clock.schedule_interval(self.update_feed, 1.0/30.0)
        else:
            print("[UI] Error: Camera could not be opened. Check permissions or connection.")
    
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
            
        # 3. Release Camera
        if self.capture:
            self.capture.release()
            self.capture = None
            print("[UI] Camera released.")
            
    def update_feed(self, dt):
        """
        Reads a frame from OpenCV and updates the Kivy Image widget.
        """
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                # Flip: OpenCV is BGR, Kivy needs RGB. Also flip vertically.
                # 0 = Vertical Flip (Kivy coordinates are bottom-up, so this fixes the display)
                buffer = cv2.flip(frame, 0).tobytes()
                
                # Create Texture
                texture = Texture.create(
                    size=(frame.shape[1], frame.shape[0]),
                    colorfmt='bgr'
                )
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                
                # Update the widget
                if self.ids.get('camera_preview'):
                    self.ids.camera_preview.texture = texture
            else:
                # for debugging if the camera drops out
                print("[UI] From read failed")
            
    def handle_load_cell_trigger(self, instance, weight):
        """
        Logic for when the load cell is triggered.
        """
        print(f"[UI] Capture Screen detected load cell trigger: {weight}")
        
        # 1. Save the *current* frame from the camera
        self.save_current_frame()
        
        # 2. Move to processing (simulated)
        Clock.schedule_once(lambda dt: self.go_to('tool confirm screen'), 1)
    
    # --- DEV - CAPTURE WITH BUTTON - REMOVE LATER --- 
    def capture_btn(self, weight):
        """
        Logic for when the DEV - CAPTURE button is pressedd
        """
        print(f"[UI] Capture Screen detected CAPTURE BTN trigger: {weight}")
        
        # 1. Save the *current* frame from the camera
        self.save_current_frame()
        
        # 2. Move to processing (simulated)
        Clock.schedule_once(lambda dt: self.go_to('tool confirm screen'), 1)
    
    def save_current_frame(self):
        """
        Grabs the current frame and saves it to disk for the API to upload.
        """
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                filename = "capture.jpg" # rename the file name to ucid and transaction
                # Save the raw frame (not flipped) so the ML model sees it normally
                cv2.imwrite(filename, frame)
                print(f"[UI] Image saved to {filename}")
                
                # Store path in session so API can find it later
                app = App.get_running_app()
                if hasattr(app, 'session'):
                    app.session.current_image_path = os.path.abspath(filename)