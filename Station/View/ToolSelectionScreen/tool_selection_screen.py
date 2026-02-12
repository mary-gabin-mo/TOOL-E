from kivy.app import App
from kivy.properties import ObjectProperty
from kivymd.uix.list import TwoLineListItem

from View.baseScreen import BaseScreen

class ToolSelectionScreen(BaseScreen):
    
    selected_tool = ObjectProperty(None, allownone=True)
    
    def on_enter (self):
        """Called every time the screen is displayed."""
        self.selected_tool = None
        self.ids.next_button.disabled = True
        self.populate_list()
        
    def populate_list(self):
        """Clears the list and re-adds tool items using API data."""
        # 1. Clear previous items so we don't duplicate
        scroll_list = self.ids.tool_list_container
        scroll_list.clear_widgets()
        
        # 2. Fetch data from API
        app = App.get_running_app()
        all_tools = app.api_client.get_tools()
        
        if not all_tools:
            scroll_list.add_widget(TwoLineListItem(text="No API tools found", secondary_text="Check server connection"))
        
        else:
            # 3. Create items
            for tool_obj in all_tools:
                # Display name and status
                item = TwoLineListItem(
                    text=f"{tool_obj['name']} (ID: {tool_obj['id']})",
                    secondary_text=f"Status: {tool_obj['status']} | Available: {tool_obj['available_quantity']}"
                )
                
                # bind the click event
                item.bind(on_release=lambda x, t=tool_obj: self.on_tool_selected(x, t))
                
                # Add to the scroll view
                scroll_list.add_widget(item)

        # 4. Add "Other" Option to the bottom
        other_tool = {"id": 0, "name": "Other", "status": "Manual", "available_quantity": "-"}
        other_item = TwoLineListItem(
            text="Other / Not Listed",
            secondary_text="Select this if you can't find the tool"
        )
        other_item.bind(on_release=lambda x, t=other_tool: self.on_tool_selected(x, t))
        scroll_list.add_widget(other_item)
            
    def on_tool_selected(self, item_widget, tool_data):
        """
        Receives the full tool dictionary
        """
        print(f"[UI] User manually selected: {tool_data.get('name')} (ID: {tool_data.get('id')})")
        
        self.selected_tool = tool_data
        self.ids.next_button.disabled = False
        
        # Visual feedback: Reset all items text color
        for child in self.ids.tool_list_container.children:
            child.theme_text_color = "Primary"
            # child.text_color = (0, 0, 0, 1)
            
        # Highlight selected
        item_widget.theme_text_color = "Custom"
        item_widget.text_color = (0, 0, 1, 1) # Blue
        
    def confirm_scan_more(self):
        app = App.get_running_app()
        if hasattr(app, 'session'):
            # Use the session method we defined earlier
            app.session.confirm_current_tool(self.selected_tool['name'])
        self.go_to('capture screen') 
        
    def proceed(self):
        """
        User clicked Next. Confirm this tool and save to transaction list.
        Compatible with both 'Camera Flow' and 'Dev Flow'.
        """
        app = App.get_running_app()
        if hasattr(app, 'session'):
            session = app.session
            
            # DEV MODE SUPPORT: 
            # If we came here directly (skipping camera), there is no 'current_transaction'.
            # We must start one artificially so 'confirm' has something to work with.
            if not session.current_transaction:
                print("[UI] Dev Mode: Creating dummy transaction for manual selection.")
                
                from datetime import datetime
                
                # 1. Generate Timestamp ID (Same format as CaptureScreen)
                now = datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                milliseconds = int(now.microsecond / 1000)
                timestamp_id = f"{timestamp}-{milliseconds:03d}"
                
                # 2. Create Filename (Placeholder)
                filename = f"{timestamp_id}.jpg" 
                
                session.start_new_transaction(timestamp_id, filename)

            # Now we can safely confirm
            session.confirm_current_tool(self.selected_tool['name'])
            
        # Navigate to completion screen
        self.go_to('transaction confirm screen') 
