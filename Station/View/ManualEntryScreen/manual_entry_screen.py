from View.baseScreen import BaseScreen
from kivy.app import App
import time

class ManualEntryScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Aggressive debouncing for touchscreen - Pi is slow
        self._last_input_time = 0
        self._debounce_delay = 0.35  # 350ms debounce for Pi touchscreen

    def on_leave(self):
        self.clear_input()

    def _check_debounce(self):
        """Check if enough time has passed since last input"""
        current_time = time.time()
        if current_time - self._last_input_time >= self._debounce_delay:
            self._last_input_time = current_time
            return True
        return False

    def add_digit(self, digit):
        """Add a digit to the input with debouncing"""
        if not self._check_debounce():
            return
        
        # Limit length to avoid infinite strings
        current_text = self.ids.ucid_input.text
        if len(current_text) < 8: 
            self.ids.ucid_input.text += digit
            print(f"[INPUT] Added digit: {digit}")

    def clear_input(self):
        """Clear all input"""
        if not self._check_debounce():
            return
        self.ids.ucid_input.text = ""
        print("[INPUT] Cleared input")

    def delete_last(self):
        """Remove the last character from the UCID input."""
        if not self._check_debounce():
            return
        current_text = self.ids.ucid_input.text
        if len(current_text) > 0:
            self.ids.ucid_input.text = current_text[:-1]
            print(f"[INPUT] Deleted character, now: {self.ids.ucid_input.text}")

    def submit_ucid(self):
        ucid = self.ids.ucid_input.text
        print(f"Submitting UCID: {ucid}")
        
        app = App.get_running_app()
        result = app.api_client.validate_user(ucid)
        if result['success'] == True:
            # Save the user info to the session once validated
            app.session.user_data = result['user']
            # Save the specific ID (mapping API 'ucid' to session 'user_id')
            app.session.user_id = str(result['user'].get('ucid', ''))
            self.go_to('action selection screen')
            
        else:
            # if the validation failed, show the appropriate error message
            error_screen = self.manager.get_screen('user error screen')
            error_screen.set_error_message(result['error'])
            self.go_to('user error screen')
