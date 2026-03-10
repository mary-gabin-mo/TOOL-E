from View.baseScreen import BaseScreen
from kivy.app import App

import threading
from kivy.clock import mainthread

class ManualEntryScreen(BaseScreen):

    def on_leave(self):
        self.clear_input()

    def add_digit(self, digit):
        # Limit length to avoid infinite strings
        current_text = self.ids.ucid_input.text
        if len(current_text) < 8: 
            self.ids.ucid_input.text += digit

    def clear_input(self):
        self.ids.ucid_input.text = ""

    def delete_last(self):
        """Remove the last character from the UCID input."""
        current_text = self.ids.ucid_input.text
        if len(current_text) > 0:
            self.ids.ucid_input.text = current_text[:-1]

    def submit_ucid(self):
        ucid = self.ids.ucid_input.text
        print(f"Submitting UCID: {ucid}")
        
        # Disable button/input during loading
        self.ids.ucid_input.disabled = True
        
        # Run API in thread to prevent UI freezing
        threading.Thread(target=self._submit_ucid_thread, args=(ucid,)).start()

    def _submit_ucid_thread(self, ucid):
        app = App.get_running_app()
        result = app.api_client.validate_user(ucid)
        self._handle_validation_result(result)

    @mainthread
    def _handle_validation_result(self, result):
        # Re-enable input
        self.ids.ucid_input.disabled = False
        app = App.get_running_app()
        
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
