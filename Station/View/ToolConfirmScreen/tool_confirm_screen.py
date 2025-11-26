from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class ToolConfirmScreen(MDScreen):
    def go_to_main(self):
        """Navigate to the Welcome screen."""
        self.go_to('welcome screen')
        
    def go_to(self, screen):
        self.manager.current = screen