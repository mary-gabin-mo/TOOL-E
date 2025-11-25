from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class ActionSelectionScreen(MDScreen):
    def go_to_main(self):
        """Navigate to the Welcome screen."""
        self.manager.current = 'welcome screen'
    
    def borrow_tool(self):
        """persist borrow state"""
        print("BORROWING")
    
    def return_tool(self):
        """persist return state"""
        print("RETURNING")