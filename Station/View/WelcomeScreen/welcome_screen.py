
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from View.baseScreen import BaseScreen
import threading

class WelcomeScreen(BaseScreen):
    
    def on_enter(self):
        """
        Reset state when entering screen.
        """
        self.set_loading_state(False)
        
        # Start listening to hardware
        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            # Bind the 'on_card_scanned' event to our function
            app.hardware.bind(on_card_scanned=self.handle_card_scan)
        
    def on_leave(self):
        """
        Stop listening so this logic doesn't get triggered on other screens.
        """
        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            app.hardware.unbind(on_card_scanned=self.handle_card_scan)
           
    @mainthread
    def set_loading_state(self, is_loading):
        """
        Toggles between the 'Instructions' and 'Loading Spinner' views.
        """       
        print(f"[UI] {is_loading=}")
        if is_loading:
            # Show Loading
            self.ids.instruction_box.opacity = 0
            self.ids.loading_box.opacity = 1
            self.ids.loading_box.height = dp(100) # Set height
            self.ids.loading_spinner.active = True
            self.ids.footer_buttons.opacity = 0 # Hide buttons so user can't click twice
            self.ids.footer_buttons.disabled = True
        else:
            # Show Instructions
            self.ids.instruction_box.opacity = 1
            self.ids.loading_box.opacity = 0
            self.ids.loading_box.height = 0 # Collapse to 0 pixels
            self.ids.loading_spinner.active = False
            self.ids.footer_buttons.opacity = 1 
            self.ids.footer_buttons.disabled = False
    
    @mainthread
    def handle_card_scan(self, instance, barcode):
        """
        Logic for when a card is detected.
        """
        print(f"[UI] Welcome Screen detected card: {barcode=}")
        
        # Update UI immediately
        self.set_loading_state(True)
        
        # Run the API call in a background thread so UI doens't freeze
        threading.Thread(target=self._validate_user_async, args=(barcode,)).start()
        
    def _validate_user_async(self, barcode):
        """BACKGROUND TASK: Runs in a separate thread"""
        app = App.get_running_app()
        result = app.api_client.validate_user(barcode)
        
        # When done, pass results back to the main thread
        self._handle_validation_result(result)
        
    @mainthread
    def _handle_validation_result(self, result):
        app = App.get_running_app()
        """RESULT HANDLER: Runs back on the Main UI Thread"""
        if result['success']: # Success Logic
            # Once the user is validated, save the user info in SessionManager.
            app.session.user_data = result['user']
            # Save the specific ID (mapping API 'ucid' to session 'user_id')
            app.session.user_id = str(result['user'].get('ucid', ''))
            self.go_to('action selection screen')
        else: # Failure Logic
            # if the validation failed, show the appropriate error message
            error_screen = self.manager.get_screen('user error screen')
            error_screen.set_error_message(result['error'])
            self.go_to('user error screen')
        
    def go_to(self, screen):
        self.manager_screens.transition.direction = 'left'
        self.manager_screens.current = screen

        
