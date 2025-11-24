import importlib
import os
import platform

# --- Config - must run before other Kivy imports ---
from kivy.config import Config 
from kivy.core.window import Window

IS_RASPBERRY_PI = platform.machine() in ("aarch64", "armv7l")

# Enable hot reload on Mac/Windows only
ENABLE_HOT_RELOAD = not IS_RASPBERRY_PI

if IS_RASPBERRY_PI:
    print("System: Raspberry Pi detected. Setting FULLSCREEN.")
    Config.set('graphics', 'fullscreen', 'auto')
    Config.set('graphics', 'window_state', 'maximized')
    Config.set('graphics', 'show_cursor', '0')
else:
    print("System: Dev Environment detected. Setting WINDOWED.")
    Config.set('graphics', 'fullscreen', '0')
    Config.set('graphics', 'width', '600')
    Config.set('graphics', 'height', '1024')
    
    Window.top = 0
    Window.left = 2000

Config.write()


# --- Local Module Imports ---
# Services 
from services.hardware import HardwareManager

if ENABLE_HOT_RELOAD:
    # --- Kivy/KivyMD imports ---
    from kivymd.tools.hotreload.app import MDApp
    from kivymd.uix.screenmanager import MDScreenManager

    class KioskApp(MDApp):
        KV_DIRS = [os.path.join(os.getcwd(), "View")]

        def build_app(self) -> MDScreenManager:
            
            import View.screens
            
            self.title = "TOOL-E Kiosk"
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "Blue"
            
            # Initialize Services (Singleton)
            if not hasattr(self, 'hardware'):
                self.hardware = HardwareManager()
            # if not hasattr(self, 'api_client'):
            #     self.api_client = APIClient()
            
            self.manager_screens = MDScreenManager()
            Window.bind(on_key_down=self.on_keyboard_down)
            importlib.reload(View.screens)
            screens = View.screens.screens
            
            for i, name_screen in enumerate(screens.keys()):
                view = screens[name_screen]["view"]()
                view.manager_screens = self.manager_screens
                view.name = name_screen
                self.manager_screens.add_widget(view)
            
            return self.manager_screens
        
        def on_keyboard_down(self, window, keyboard, keycode, text, modifiers) -> None:
            if ("meta" in modifiers or "ctrl" in modifiers) and text == "r":
                self.rebuild()
                
        def on_start(self):
            print("App Started.")
            
        def on_stop(self):
            print("App Stopping...")
            if hasattr(self, 'hardware') and IS_RASPBERRY_PI:
                try:
                    import RPi.GPIO as GPIO
                    GPIO.cleanup()
                except:
                    pass
                
else:
    # --- Kivy/KivyMD imports ---
    from kivymd.app import MDApp
    from kivymd.uix.screenmanager import MDScreeenManager
    
    from View.screens import screens
    
    class KioskApp(MDApp):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.load_all_kv_files(self.directory)
            self.manager_screens = MDScreenManager()
            
        def build(self) -> MDScreenManager:
            
            self.title = "TOOL-E Kiosk"
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "Blue"
            
            # Initialize Services (Singleton)
            if not hasattr(self, 'hardware'):
                self.hardware = HardwareManager()
            # if not hasattr(self, 'api_client'):
            #     self.api_client = APIClient()
            
            self.generate_application_screens()
            return self.manager_screens
        
        def generate_application_screens(self) -> None:
            for i, name_screen in enumerate(screens.keys()):
                view = screens[name_screen]["view"]()
                view.manager_screens = self.manager_screens
                view.name = name_screen
                self.manager_screens.add_widget(view)
                
        def on_start(self):
            print("App Started.")
            
        def on_stop(self):
            print("App Stopping...")
            if hasattr(self, 'hardware') and IS_RASPBERRY_PI:
                try:
                    import RPi.GPIO as GPIO
                    GPIO.cleanup()
                except:
                    pass

KioskApp().run()
