from kivy.app import App
from kivymd.uix.list import OneLineListItem
from View.baseScreen import BaseScreen
from widgets.calendar_popup import CalendarPopup
from datetime import datetime, date

class TransactionConfirmScreen(BaseScreen):
    
    return_date = None
    purpose = None # 'Academic Course' or 'Personal Project'
    
    def on_enter(self):
        """Reset state when entering screen."""
        self.return_date = None
        
        app = App.get_running_app()
        transaction_type = getattr(app.session, 'transaction_type', 'borrow')
        
        # For returns, we don't need a return date - skip directly to finish
        if transaction_type == "return":
            self.ids.date_box.opacity = 0  # Hide date selector
            self.ids.date_box.size_hint_y = 0
            self.ids.confirm_finish_btn.disabled = False
            self.ids.confirm_finish_btn.text = "CONFIRM RETURN"
        else:
            # For borrows, show date selector
            self.ids.date_box.opacity = 1
            self.ids.date_box.size_hint_y = None
            self.ids.confirm_finish_btn.disabled = True
            self.ids.confirm_finish_btn.text = "CONFIRM CHECKOUT"
            
            # Reset the red border box visuals
            self.ids.date_box.line_color = (1,0,0,1) # Red border
            self.ids.date_label.text = "Tap to select Return Date"
            self.ids.date_label.text_color = (0.5, 0.5, 0.5, 1)
        
        # Load tool info from session
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
        
        self.check_can_finish()
        
    def select_purpose(self, selected_purpose):
        self.purpose = selected_purpose
        
        # Update colors
        if selected_purpose == "Academic Course":
            self.ids.btn_academic.md_bg_color = (0.2, 0.6, 0.8, 1) # Blue
            self.ids.btn_academic.text_color = (1, 1, 1, 1)        # White text
            self.ids.btn_personal.md_bg_color = (0.9, 0.9, 0.9, 1) # Grey
            self.ids.btn_personal.text_color = (0, 0, 0, 1)        # Black text
        else:
            self.ids.btn_personal.md_bg_color = (0.2, 0.6, 0.8, 1) # Blue
            self.ids.btn_personal.text_color = (1, 1, 1, 1)        # White text
            self.ids.btn_academic.md_bg_color = (0.9, 0.9, 0.9, 1) # Grey
            self.ids.btn_academic.text_color = (0, 0, 0, 1)        # Black text
            
        self.check_can_finish()

    def check_can_finish(self):
        # Enable the final button only if both date and purpose are selected
        if self.return_date and self.purpose:
            self.ids.confirm_finish_btn.disabled = False
        else:
            self.ids.confirm_finish_btn.disabled = True

    def finish_transaction(self):
        app = App.get_running_app()
        
        # For returns, use current date/time; for borrows, use selected return date
        if app.session.transaction_type == "return":
            formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Return Transaction Confirmed at: {formatted_date}")
        else:
            print(f"Checkout Transaction Confirmed! Return Date: {self.return_date}")
            # Format Date for Backend (YYYY-MM-DD HH:MM:SS)
            if isinstance(self.return_date, date) and not isinstance(self.return_date, datetime):
                formatted_date = f"{self.return_date.strftime('%Y-%m-%d')} 12:00:00"
            else:
                formatted_date = self.return_date.strftime("%Y-%m-%d %H:%M:%S")

        # Safe User ID retrieval
        user_id = getattr(app.session, 'user_id', '')
        user_dict = app.session.user_data or {}

        if not user_id and user_dict:
             # Fallback: try to get ID from the user dictionary if user_id property is empty
             # API returns 'ucid', checking both just in case
             user_id = user_dict.get('ucid') or user_dict.get('id', '')

        # Get User Name (First + Last)
        first_name = user_dict.get('first_name', '')
        last_name = user_dict.get('last_name', '')
        user_name = f"{first_name} {last_name}".strip()

        # Construct the final payload for the API
        final_payload = {
            "user_id": str(user_id), 
            "user_name": user_name or "Unknown User",
            "return_date": formatted_date,
            "purpose": self.purpose,
            "transactions": getattr(app.session, 'transactions', [])
        }
        
        print(f"[UI] Submitting Transaction via APIClient...")

        # Call API logic using the centralized API Client
        response = app.api_client.submit_transaction(final_payload)
             
        if response.get('success'):
             print("Transaction Success")
             # Navigate to appropriate confirmation screen based on transaction type
             if app.session.transaction_type == "return":
                 self.go_to('return confirmation screen')
             else:
                 self.go_to('checkout confirmation screen')
        else:
             print(f"Transaction Failed: {response.get('error')}")
             # You might want to add a UI popup here to alert the user

#Submitting Transaction: {'user_id': '30113779', 'user_name': 'Hongwoo Yoon', 'return_date': '2026-03-25 12:00:00', 'purpose': 'Academic Course', 'transactions': [{'transaction_id': '20260306_154121-492', 'img_filename': '20260306_154121-492.jpg', 'tool_name': 'Hot Glue Gun', 'classification_correct': False}]}