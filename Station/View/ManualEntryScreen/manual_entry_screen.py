from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class ManualEntryScreen(MDScreen):
    def go_to_main(self):
        """Navigate to the Welcome screen."""
        self.manager.current = 'welcome screen'