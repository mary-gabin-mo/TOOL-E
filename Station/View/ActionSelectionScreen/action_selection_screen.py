
from kivy.app import App
from kivy.clock import Clock

from View.baseScreen import BaseScreen

class ActionSelectionScreen(BaseScreen):
    
    def select_borrow(self):
        """persist borrow state"""
        app = App.get_running_app()
        app.session.set_transaction_type("borrow")
        self.manager.transition.direction = 'left'
        self.manager.current = 'capture screen'
        print("BORROWING")
    
    def select_return(self):
        """persist return state"""
        app = App.get_running_app()
        app.session.set_transaction_type("return")
        self.manager.transition.direction = 'left'
        self.manager.current = 'capture screen'
        print("RETURNING")