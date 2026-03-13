from kivy.app import App
from kivy.properties import ObjectProperty, DictProperty, StringProperty, ListProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
import threading
from kivy.clock import mainthread

from View.baseScreen import BaseScreen

class SelectableToolItem(RecycleDataViewBehavior, ButtonBehavior, BoxLayout):
    text = StringProperty('')
    secondary_text = StringProperty('')
    tool_data = DictProperty()
    text_color = ListProperty([0, 0, 0, 1])

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def handle_selection(self):
        app = App.get_running_app()
        # Find the active screen using app.manager_screens
        if hasattr(app, 'manager_screens'):
            screen = app.manager_screens.get_screen('tool select screen')
            if screen:
                screen.on_tool_selected(self, self.tool_data)

class ToolSelectionScreen(BaseScreen):
    
    selected_tool = ObjectProperty(None, allownone=True)
    
    def on_enter (self):
        """Called every time the screen is displayed."""
        self.selected_tool = None
        self.ids.next_button.disabled = True
        self.populate_list()
        
    def populate_list(self):
        """Clears the list and fetches tool items using API data in a thread."""
        tool_rv = self.ids.tool_recycle_view
        
        # Show a loading placeholder
        tool_rv.data = [{"text": "Loading tools...", "secondary_text": "Please wait", "tool_data": {}, "text_color": [0, 0, 0, 1]}]
        
        threading.Thread(target=self._fetch_tools_thread).start()
        
    def _fetch_tools_thread(self):
        app = App.get_running_app()
        all_tools = app.api_client.get_tools()
        self._update_ui_with_tools(all_tools)
        
    @mainthread
    def _update_ui_with_tools(self, all_tools):
        # 1. Clear previous items so we don't duplicate
        tool_rv = self.ids.tool_recycle_view
        
        if not all_tools:
            tool_rv.data = [{"text": "No API tools found", "secondary_text": "Check server connection", "tool_data": {}, "text_color": [0, 0, 0, 1]}]
        
        else:
            rv_data = []
            # 3. Create items
            for tool_obj in all_tools:
                rv_data.append({
                    "text": f"{tool_obj['name']} (ID: {tool_obj['id']})",
                    "secondary_text": f"Status: {tool_obj['status']} | Available: {tool_obj['available_quantity']}",
                    "tool_data": tool_obj,
                    "text_color": [0, 0, 0, 1]
                })

            # 4. Add "Other" Option to the bottom
            other_tool = {"id": 0, "name": "Other", "status": "Manual", "available_quantity": "-"}
            rv_data.append({
                "text": "Other / Not Listed",
                "secondary_text": "Select this if you can't find the tool",
                "tool_data": other_tool,
                "text_color": [0, 0, 0, 1]
            })
            
            tool_rv.data = rv_data
            
    def on_tool_selected(self, item_widget, tool_data):
        """
        Receives the full tool dictionary
        """
        if not tool_data:
            return
            
        print(f"[UI] User manually selected: {tool_data.get('name')} (ID: {tool_data.get('id')})")
        
        self.selected_tool = tool_data
        self.ids.next_button.disabled = False
        
        # Visual feedback: Reset all items text color in data model
        rv = self.ids.tool_recycle_view
        for i, item in enumerate(rv.data):
            if item.get('tool_data', {}).get('id') == tool_data.get('id'):
                rv.data[i]['text_color'] = [0, 0, 1, 1]  # Blue
            else:
                rv.data[i]['text_color'] = [0, 0, 0, 1]  # Black
        
        rv.refresh_from_data()
        
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
            # If classification_correct has not been set (e.g., coming from Dev Mode or unexpected flow),
            # default to False because the user had to manually select it.
            if session.current_transaction.get('classification_correct') is None:
                 session.set_classification_correct(False)
                 
            session.confirm_current_tool(self.selected_tool['name'])
            
        # Navigate to completion screen
        self.go_to('transaction confirm screen') 
