from kivy.app import App
from kivymd.uix.list import OneLineListItem
from View.baseScreen import BaseScreen
from widgets.calendar_popup import CalendarPopup

class TransactionConfirmScreen(BaseScreen):
    
    return_date = None
    
    def on_enter(self):
        """Reset state when entering screen."""
        self.return_date = None
        self.ids.confirm_finish_btn.disabled = True
        
        # Reset the red border box visuals
        self.ids.date_box.line_color = (1,0,0,1) # Red border
        self.ids.date_label.text = "Tap to select Return Date"
        self.ids.date_label.text_color = (0.5, 0.5, 0.5, 1)
        
        # Load tool info from session
        app = App.get_running_app()
        transactions = getattr(app.session, 'transactions', [])
        
        # Clear existing items in the list
        list_container = self.ids.tool_list_container
        list_container.clear_widgets()
        
        if not transactions:
            # Fallback if list is empty (shouldn't happen in flow)
            list_container.add_widget(OneLineListItem(text="No tools scanned"))
        else:
            # Populate list with all scanned tools
            for tx in transactions:
                # Handle dictionary or simple string
                tool_name = tx.get('tool_name', 'Unknown Tool') # if isinstance(tool, dict) else str(tool)
                list_container.add_widget(OneLineListItem(text=tool_name))
        
    def open_calendar(self):
        """Open the custom popup"""
        popup = CalendarPopup(callback=self.on_date_selected)
        popup.open()
        
    def on_date_selected(self, date_obj):
        """Called by the popup when user hits Confirm."""
        self.return_date = date_obj
        
        # Save return date to session and update JSON
        app = App.get_running_app()
        app.session.return_date = date_obj
        app.session.save_to_json()
        
        # Update UI to show success
        self.ids.date_label.text = f"Returning on: {date_obj.strftime('%b %d, %Y')}"
        self.ids.date_label.text_color = (0, 0, 0, 1) # Black text
        
        # Change border from Red to Blue/Grey to indicate "Done"
        self.ids.date_box.line_color = (0.2, 0.6, 0.8, 1)
        
        # Enable the final button
        self.ids.confirm_finish_btn.disabled = False
        
    def finish_transaction(self):
        print(f"Transaction Confirmed! Date: {self.return_date}")
        
        app = App.get_running_app()
        
        # Final save to JSON before sending to server
        app.session.save_to_json()
        print(f"[TRANSACTION] Transaction ID: {app.session.transaction_id}")
        
        # Send the transaction JSON to the server
        # TODO: Implement API call to submit transaction.json to server
        # app.api_client.submit_transaction(app.session.load_from_json())
        
        # Go to confirmation screen
        self.go_to('checkout confirmation screen')