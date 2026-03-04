from kivy.app import App
from kivymd.uix.screen import MDScreen

class BaseScreen(MDScreen):
    """
    Parent class for all screens.
    Includes helper methods for navigation.
    """
    
    def go_to(self, screen_name):
        """Forward navigation (Slide Left)"""
        # 'self.manager' is automatically available in all Screens
        if self.manager:
            self.manager.transition.direction = 'left'
            self.manager.current = screen_name 
            
    def go_back(self, screen_name):
        """Backward navigation (Slide Right)"""   
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = screen_name
            
    def cancel_transaction(self):
        """
        User clicked CANCEL. Reset session and go back to welcome screen.
        """
        app = App.get_running_app()
        if hasattr(app, 'session'):
            app.session.reset()
        self.go_back('welcome screen')
