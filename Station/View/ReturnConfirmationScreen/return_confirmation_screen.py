from View.baseScreen import BaseScreen

class ReturnConfirmationScreen(BaseScreen):
    
    def on_enter(self):
        """Called when the screen is displayed."""
        from kivy.app import App
        app = App.get_running_app()
        
        # Display confirmation message
        # Optionally show number of tools returned
        num_tools = len(getattr(app.session, 'transactions', []))
        
        if num_tools > 0:
            tool_text = "tool" if num_tools == 1 else "tools"
            self.ids.message_display.text = f"Successfully returned {num_tools} {tool_text}!"
        else:
            self.ids.message_display.text = "Return confirmed!"
    
    def return_to_menu(self):
        """Clear session data and return to welcome screen."""
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
        app.session.transactions = []
        app.session.current_transaction = {}
        app.session.transaction_type = "borrow"  # Reset to default
        
        # Navigate to action selection screen
        self.go_to('action selection screen')
