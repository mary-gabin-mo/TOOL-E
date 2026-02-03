from View.baseScreen import BaseScreen

class CheckoutConfirmationScreen(BaseScreen):
    
    def on_enter(self):

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
        # Clear session data
        from kivy.app import App
        app = App.get_running_app()
        app.session.reset()
        
        # Navigate to welcome screen (homepage)
        self.go_to('welcome screen')
    
    def continue_with_user(self):
        """Navigate to action selection screen while keeping user logged in."""
        from kivy.app import App
        app = App.get_running_app()
        
        # Clear only transaction-specific data, keep user_data
        app.session.scanned_tools = []
        app.session.return_date = None
        app.session.transaction_type = "borrow"  # Reset to default
        
        # Navigate to action selection screen
        self.go_to('action selection screen')
