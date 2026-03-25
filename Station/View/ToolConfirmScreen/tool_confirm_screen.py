import os
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
            # Display the local full path on the screen (not the server's uuid name)
            img_path = app.session.current_transaction.get('local_img_path', app.session.current_transaction.get('img_filename', img_path))
        
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
                score_source = data.get('source')
                confidence = data.get('score', None)
                if score_source == 'manual':
                    score = "Manually selected"
                elif isinstance(confidence, (int, float)):
                    score = f"{int(confidence * 100)}% Match"
                else:
                    score = ""
        
        self.predicted_name = tool_name
        self.ids.tool_name_label.text = tool_name
        self.ids.confidence_label.text = score

    def _delete_current_image(self):
        """Delete the temporary captured image after user leaves confirmation."""
        app = App.get_running_app()
        if not hasattr(app, 'session') or not app.session.current_transaction:
            return

        img_path = app.session.current_transaction.get('img_filename')
        if img_path and os.path.isabs(img_path) and os.path.exists(img_path):
            try:
                os.remove(img_path)
                print(f"[UI] Deleted image file {img_path} after tool confirmation.")
            except Exception as e:
                print(f"[UI] Warning: could not delete image {img_path}: {e}")

    def confirm_scan_more(self):
        """
        User clicked YES. Confirm this tool and save to transaction list.
        """
        app = App.get_running_app()
        
        if hasattr(app, 'session'):
            # Preserve explicit manual-correction flag if user previously rejected prediction.
            existing_flag = app.session.current_transaction.get('classification_correct') if app.session.current_transaction else None
            if existing_flag is None:
                app.session.set_classification_correct(True)
        
        # Check if this is a return transaction
        if app.session.transaction_type == "return":
            # Mark tool as confirmed
            app.session.tool_was_confirmed = True
            self._delete_current_image()
            # Go to tool return selection screen
            self.go_to('tool return selection screen')
        else:
            # For borrows, confirm and scan more
            if hasattr(app, 'session'):
                self._delete_current_image()
                app.session.confirm_current_tool(self.predicted_name)
            self.go_to('capture screen') 
        
    def confirm_finish(self):
        """
        User clicked YES. Confirm this tool and save to transaction list.
        """
        app = App.get_running_app()
        
        if hasattr(app, 'session'):
            # Preserve explicit manual-correction flag if user previously rejected prediction.
            existing_flag = app.session.current_transaction.get('classification_correct') if app.session.current_transaction else None
            if existing_flag is None:
                app.session.set_classification_correct(True)
        
        # Check if this is a return transaction
        if app.session.transaction_type == "return":
            # Mark tool as confirmed
            app.session.tool_was_confirmed = True
            self._delete_current_image()
            # Go to tool return selection screen
            self.go_to('tool return selection screen')
        else:
            # For borrows, confirm and finish
            if hasattr(app, 'session'):
                self._delete_current_image()
                app.session.confirm_current_tool(self.predicted_name)
            self.go_to('transaction confirm screen') 

    def reject_tool(self):
        """
        User clicked NO. Go to the manual selection list or tool return selection.
        """
        app = App.get_running_app()
        
        if hasattr(app, 'session'):
            app.session.set_classification_correct(False)
        
        # Check if this is a return transaction
        if app.session.transaction_type == "return":
            # Mark tool as NOT confirmed (will show all unreturned tools)
            app.session.tool_was_confirmed = False
            self._delete_current_image()
            # Go to tool return selection screen
            self.go_to('tool return selection screen')
        else:
            # For borrows, go to manual selection
            self.go_to('tool select screen')

    def go_back_to_capture(self):
        """Back button handler for confirm screen."""
        self._delete_current_image()
        self.go_to('capture screen')
