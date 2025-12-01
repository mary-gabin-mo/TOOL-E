from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class ManualEntryScreen(MDScreen):

    def add_digit(self, digit):
        # Limit length to avoid infinite strings
        current_text = self.ids.ucid_input.text
        if len(current_text) < 8: 
            self.ids.ucid_input.text += digit

    def clear_input(self):
        self.ids.ucid_input.text = ""

    def submit_ucid(self):
        ucid = self.ids.ucid_input.text
        print(f"Submitting UCID: {ucid}")
        
        app = App.get_running_app()
        result = app.api_client.validate_user(ucid)
        if result['success']:
            # Save the user info to the session once validated
            app.session.user_data = result['data']
            
    def back_to_main(self):
        """Clear input field and navigate to the Welcome screen."""
        self.clear_input()
        self.go_back('welcome screen')
        
    def go_to(self, screen):
        self.manager_screens.transition.direction = 'left'
        self.manager_screens.current = screen
        
    def go_back(self, screen):
        self.manager_screens.transition.direction = 'right'
        self.manager_screens.current = screen