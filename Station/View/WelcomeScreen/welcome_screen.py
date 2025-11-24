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
            
    def handle_card_scan(self, instance, card_id):
        """
        Logic for when a card is detected.
        """
        print(f"[UI] Welcome Screen detected card: {card_id}")
        
        # Validate User (irl, would be an API call - for now, simulate a delay)
        Clock.schedule_once(lambda dt: self.go_to_action_selection(), 1.0)
        
    def go_to_action_selection(self):
        """Navigate to the Borrow/Return screen."""
        self.manager.current = 'action selection screen'
        
    # def go_to_manaul(self):
    #     """Navigate to Manual Entry."""
    #     self.manager.current = 'manual_entry_screen'
        