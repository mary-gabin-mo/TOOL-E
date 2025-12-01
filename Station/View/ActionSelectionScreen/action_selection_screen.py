from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class ActionSelectionScreen(MDScreen):
    def go_to_main(self):
        """Navigate to the Welcome screen."""
        app = App.get_running_app()
        app.session.reset()
        self.manager.current = 'welcome screen'
    
    def select_borrow(self):
        """persist borrow state"""
        app = App.get_running_app()
        app.session.set_transaction_type("borrow")
        self.manager.current = 'capture screen'
        print("BORROWING")
    
    def select_return(self):
        """persist return state"""
        app = App.get_running_app()
        app.session.set_transaction_type("return")
        self.manager.current = 'capture screen'
        print("RETURNING")