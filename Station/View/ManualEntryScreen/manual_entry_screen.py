from View.baseScreen import BaseScreen
from kivy.app import App
from kivy.clock import Clock

class ManualEntryScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._input_lock = False  # Prevent rapid successive inputs

    def on_leave(self):
        self.clear_input()

    def add_digit(self, digit):
        # Prevent rapid successive inputs (debouncing)
        if self._input_lock:
            return
        
        # Limit length to avoid infinite strings
        current_text = self.ids.ucid_input.text
        if len(current_text) < 8: 
            self.ids.ucid_input.text += digit
            
        # Lock input for 100ms to prevent double-clicks
        self._input_lock = True
        Clock.schedule_once(self._unlock_input, 0.1)

    def _unlock_input(self, dt):
        self._input_lock = False

    def clear_input(self):
        if self._input_lock:
            return
        self.ids.ucid_input.text = ""
        self._input_lock = True
        Clock.schedule_once(self._unlock_input, 0.1)

    def delete_last(self):
        """Remove the last character from the UCID input."""
        if self._input_lock:
            return
        current_text = self.ids.ucid_input.text
        if len(current_text) > 0:
            self.ids.ucid_input.text = current_text[:-1]
        self._input_lock = True
        Clock.schedule_once(self._unlock_input, 0.1)

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
