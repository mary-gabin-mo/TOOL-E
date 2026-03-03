from kivymd.uix.screen import MDScreen
from kivy.app import App

class UserErrorScreen(MDScreen):
    
    def set_error_message(self, message):
        """
        Updates the error label with dynamic text.
        Call this method BEFORE switching to this screen.
        """
        self.ids.error_label.text = str(message)
    def go_to_main(self):
        """Resets the session and goes back to the Welcome screen."""
        app = App.get_running_app()
        if hasattr(app, 'session'):
            app.session.reset()
            
        self.manager.current = 'welcome screen'