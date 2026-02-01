import cv2
import platform
import os
import time
import numpy as np
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
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
        app = App.get_running_app()
        
        # 1. Bind hardware Events
        if hasattr(app, 'hardware'):
            app.hardware.bind(on_load_cell_detect=self.handle_load_cell_trigger)
            
        print(f"[UI] Initializing Camera (Pi Mode: {IS_RASPBERRY_PI})...")
        
        if IS_RASPBERRY_PI:
            self.init_pi_camera()
        else:
            self.init_laptop_camera()
            
        # Start the Update Loop (30 FPS)
        self.update_event = Clock.schedule_interval(self.update_feed, 1.0/30.0)
    
    def init_pi_camera(self):
        """Native Pi 5 Camera Initialization using Picamera2"""
        try:
            from picamera2 import Picamera2
            fself.picam2 = Picamera2()
            
            # Configure: 'main' for high-res capture, 'lores' for the UI preview
            config = self.picam2.create_still_configuration(
                main={"size": (1920, 1080), "format": "RGB888"},
                lores={"size": (640, 480), "format": "RGB888"},
            )
            self.picam2.configure(config)
            self.picam2.start()
            print("[UI] Picamera2 started successfully.")
        except Exception as e:
            print("[UI] CRITICAL Picamera2 Error: {e}.")
            
    def init_laptop_camera(self):
        """Fallback to OpenCV for non-pi devices"""
        try:
            self.capture = cv2.VideoCapture(0)
            if self.capture.isOpened():
                print("[UI] Laptop Webcam opened.")
        except Exception as e:
            print(f"[UI] Webcam Error: {e}")
            
        # if IS_RASPBERRY_PI:
        #     try:
        #         # Option A: standard index 0 (works on many Pi setups if legacy camera support is enabled)
        #         self.capture = cv2.VideoCapture(0)

        #         # Check if it actually opened
        #         # Validate that we can actually read a frame.
        #         if self.capture.isOpened():
        #             ret, test_frame = self.capture.read()
        #             if not ret:
        #                 print("[UI] Index 0 opened but failed to read frame. Releasing...")
        #                 self.capture.release()
        #                 self.capture = None
                    
        #         # Option B: Pi 5 / libcamera GStreamer Pipeline
        #         # tells OpenCV to use the GStreamer backend to talk to libcamerasrc directly
        #         if self.capture is None or not self.capture.isOpened():
        #             print("[UI] Attempting GStreamer pipeline for libcamera...")
                    
        #             pipeline = (
        #                 "libcamerasrc ! "
        #                 "video/x-raw, width=640, height=480, framerate=30/1 ! "
        #                 "videoconvert ! "
        #                 "appsink"
        #             )
        #             self.capture = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            
        #     except Exception as e:
        #         print(f"[UI] CRITICAL Error initializing Pi Camera: {e}")
        # else:
        #     # On Mac/Windows/Linux Desktop -> Use Laptop Webcam
        #     print(f"[UI] Running on Desktop/Laptop. Initializing default Webcam for testing...")
        #     # Index 0 is usually the built-in webcam
        #     self.capture = cv2.VideoCapture(0)
            
        # # 3. Start the Update Loop (30 FPS)
        # if self.capture and self.capture.isOpened():
        #     print("[UI] Camera opened successfully.")
        #     self.update_event = Clock.schedule_interval(self.update_feed, 1.0/30.0)
        # else:
        #     print("[UI] Error: Camera could not be opened. Check permissions or connection.")
    
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
            
    def update_feed(self, dt):
        """
        Reads a frame from OpenCV and updates the Kivy Image widget.
        """
        frame = None
        
        # 1. Get the frame (as numpy array)
        if IS_RASPBERRY_PI and self.picam2:
            # CApture from the law-res stream for speed
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
            texture.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            
            # Update Widget
            if self.ids.get('camera_preview'):
                self.ids.camera_preview.texture = texture
            
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
        Save high-res photo and resize using the PIL logic
        """
        filename = "capture_example.jpg"
        
        try:
            if IS_RASPBERRY_PI and self.picam2:
                # Capture High Res from 'main' stream
                self.picam2.capture_file(filename)
                print(f"[UI] Raw Pi image saved to {filename}")
                self.process_image_pil(filename)
                
            elif self.capture:
                # Laptop Capture
                ret, frame = self.capture.read()
                if ret:
                    cv2.imwrite(filename, frame)
                    self.process_image_pil(filename)
                    
            # Save path to session
            app = App.get_running_app()
            if hasattr(app, 'session'):
                app.session.current_image_path = os.path.abspath(filename)
                
        except Exception as e:
            print(f"[UI] Save Error: {e}")
            
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