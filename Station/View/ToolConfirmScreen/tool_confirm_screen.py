from kivy.app import App
from View.baseScreen import BaseScreen

class ToolConfirmScreen(BaseScreen):
    
    predicted_name = None

    def on_enter(self):
        """
        Populate the UI with data from the Session when the screen opens.
        """
        app = App.get_running_app()
        
        # 1. Get the Image Path from the current transaction
        # Default to a placeholder if missing
        img_path = "assets/images/logo_white.png"
        if hasattr(app, 'session') and app.session.current_transaction:
            img_path = app.session.current_transaction.get('img_filename', img_path)
        
        self.ids.tool_image.source = img_path
        self.ids.tool_image.reload() # Force reload if file changed

        # 2. Get the Prediction from the API result
        # We assume CaptureScreen saved the API result to 'session.identified_tool_data'
        tool_name = "Unknown Tool"
        score = ""
        
        if hasattr(app, 'session') and hasattr(app.session, 'identified_tool_data'):
            data = app.session.identified_tool_data
            if data:
                tool_name = data.get('prediction', 'Unknown')
                confidence = data.get('score', 0)
                score = f"{int(confidence * 100)}% Match"
        
        self.predicted_name = tool_name
        self.ids.tool_name_label.text = tool_name
        self.ids.confidence_label.text = score

    def confirm_scan_more(self):
        """
        User clicked YES. Confirm this tool and save to transaction list.
        """
        app = App.get_running_app()
        
        # Check if this is a return transaction
        if app.session.transaction_type == "return":
            # Mark tool as confirmed
            app.session.tool_was_confirmed = True
            # Go to tool return selection screen
            self.go_to('tool return selection screen')
        else:
            # For borrows, confirm and scan more
            if hasattr(app, 'session'):
                app.session.confirm_current_tool(self.predicted_name)
            self.go_to('capture screen') 
        
    def confirm_finish(self):
        """
        User clicked YES. Confirm this tool and save to transaction list.
        """
        app = App.get_running_app()
        
        # Check if this is a return transaction
        if app.session.transaction_type == "return":
            # Mark tool as confirmed
            app.session.tool_was_confirmed = True
            # Go to tool return selection screen
            self.go_to('tool return selection screen')
        else:
            # For borrows, confirm and finish
            if hasattr(app, 'session'):
                app.session.confirm_current_tool(self.predicted_name)
            self.go_to('transaction confirm screen') 

    def reject_tool(self):
        """
        User clicked NO. Go to the manual selection list or tool return selection.
        """
        app = App.get_running_app()
        
        # Check if this is a return transaction
        if app.session.transaction_type == "return":
            # Mark tool as NOT confirmed (will show all unreturned tools)
            app.session.tool_was_confirmed = False
            # Go to tool return selection screen
            self.go_to('tool return selection screen')
        else:
            # For borrows, go to manual selection
            self.go_to('tool select screen')
