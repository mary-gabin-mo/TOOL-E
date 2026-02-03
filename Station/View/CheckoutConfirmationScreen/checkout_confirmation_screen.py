from View.baseScreen import BaseScreen

class CheckoutConfirmationScreen(BaseScreen):
    
    def on_enter(self):
        """Display the confirmation date when entering screen."""
        # Get the date from the session or previous screen
        from kivy.app import App
        app = App.get_running_app()
        
        # Get the return date from session if available
        return_date = getattr(app.session, 'return_date', None)
        
        if return_date:
            date_str = return_date.strftime('%B %d, %Y')
            self.ids.date_display.text = f"Check confirmed for this date:\n{date_str}"
        else:
            self.ids.date_display.text = "Check confirmed!"
    
    def return_to_menu(self):
        """Navigate back to the welcome screen (homepage)."""
        # Clear session data
        from kivy.app import App
        app = App.get_running_app()
        app.session.reset()
        
        # Navigate to welcome screen (homepage)
        self.go_to('action selection screen')
