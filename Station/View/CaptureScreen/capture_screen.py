from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class CaptureScreen(MDScreen):
    
    def on_enter(self):
        """
        Called when this screen is displayed.
        Starts listeining to hardware events here.
        """
        app = App.get_running_app()
        
        if hasattr(app, 'hardware'):
            # Bind 'on_load_cell_detect' event
            app.hardware.bind(on_load_cell_detect=self.handle_load_cell_trigger)
    
    def on_leave(self):
        """
        Called when leaving this screen.
        Stop listening so this logic doesn't get triggered on other screens.
        """
        app = App.get_running_app()
        
        if hasattr(app, 'hardware'):
            # Unbind 'on_load_cell_detect' event
            app.hardware.unbind(on_load_cell_detect=self.handle_load_cell_trigger)
            
    def handle_load_cell_trigger(self, instance, weight):
        """
        Logic for when the load cell is triggered.
        """
        print(f"[UI] Capture Screen detected load cell trigger: {weight}")
        
        ##### ADD IMAGE CAPTURE LOGIC HERE #####
        
        # For now, simulate a delay
        Clock.schedule_once(lambda dt: self.go_to('tool confirm screen'), .5)
    
    def go_to_main(self):
        """Navigate to the Welcome screen."""
        self.go_to('welcome screen')
        
    def go_to(self, screen):
        self.manager.current = screen