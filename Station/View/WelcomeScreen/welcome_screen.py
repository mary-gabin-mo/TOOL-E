from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.clock import Clock

class WelcomeScreen(MDScreen):
    
    def on_enter(self):
        """
        Called when this screen is displayed.
        Starts listening to hardware evenets here.        
        """
        app = App.get_running_app()
        
        if hasattr(app, 'hardware'):
            # Bind the 'on_card_scanned' event to our function
            app.hardware.bind(on_card_scanned=self.handle_card_scan)
        
    def on_leave(self):
        """
        Called when leaving this screen.
        Stop listening so this logic doesn't get triggered on other screens.
        """
        app = App.get_running_app()
        if hasattr(app, 'hardware'):
            app.hardware.unbind(on_card_scanned=self.handle_card_scan)
            
    def handle_card_scan(self, instance, barcode):
        """
        Logic for when a card is detected.
        """
        print(f"[UI] Welcome Screen detected card: {barcode=}")
        
        ### UNCOMMENT THE BELOW LOGIC ONCE API IS CONNECTED ### 
        app = App.get_running_app()
        result = app.api_client.validate_user(barcode)
        if result['success'] == True:
            # Once the user is validated, save the user info in SessionManager.
            app.session.user_data = result['data']
            self.go_to('action selection screen')
        else:
            # if the validation failed, show the appropriate error message
            error_screen = self.manager.get_screen('user error screen')
            error_screen.set_error_message(result['error'])
            self.go_to('user error screen')
        
        # for dev, simulate a delay
        # Clock.schedule_once(lambda dt: self.go_to_action_selection(), .5)
        
    def go_to(self, screen):
        self.manager_screens.transition.direction = 'left'
        self.manager_screens.current = screen

        