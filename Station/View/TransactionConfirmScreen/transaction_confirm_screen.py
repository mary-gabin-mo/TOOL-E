from kivy.app import App
from kivymd.uix.list import OneLineListItem
from View.baseScreen import BaseScreen
from widgets.calendar_popup import CalendarPopup
from datetime import datetime, date

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
        
        # Format Date for Backend (YYYY-MM-DD HH:MM:SS)
        # If only a date is provided, default to noon or end of day
        if isinstance(self.return_date, date) and not isinstance(self.return_date, datetime):
             formatted_date = f"{self.return_date.strftime('%Y-%m-%d')} 12:00:00"
        else:
             formatted_date = self.return_date.strftime("%Y-%m-%d %H:%M:%S")

        # Safe User ID retrieval
        user_id = getattr(app.session, 'user_id', '')
        if not user_id and app.session.user_data:
             # Fallback: try to get ID from the user dictionary if user_id property is empty
             user_id = app.session.user_data.get('id', '')

        # Construct the final payload for the API
        final_payload = {
            "user_data": app.session.user_data, # Assuming this is stored
            "return_date": str(self.return_date),
            "transactions": app.session.transactions
        }
        
        print(f"[UI] Submitting Transaction via APIClient...")

        # Call API logic using the centralized API Client
        response = app.api_client.submit_transaction(final_payload)
             
        if response.get('success'):
             print("Transaction Success")
             # Go to confirmation screen only on success
             self.go_to('checkout confirmation screen')
        else:
             print(f"Transaction Failed: {response.get('error')}")
             # You might want to add a UI popup here to alert the user