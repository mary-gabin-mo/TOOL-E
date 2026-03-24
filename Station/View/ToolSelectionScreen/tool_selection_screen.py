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
    bg_color = ListProperty([1, 1, 1, 1])

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
        app = App.get_running_app()
        if hasattr(app, 'session') and app.session.transaction_type == "return":
            print("[UI] Guard: return flow cannot use ToolSelectionScreen. Redirecting.")
            self.go_to('tool return selection screen')
            return

        self.selected_tool = None
        self.ids.next_button.disabled = True
        self.populate_list()
        
    def populate_list(self):
        """Clears the list and fetches tool items using API data in a thread."""
        tool_rv = self.ids.tool_recycle_view
        
        # Show a loading placeholder
        tool_rv.data = [{"text": "Loading tools...", "secondary_text": "Please wait", "tool_data": {}, "bg_color": [1, 1, 1, 1]}]
        
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
            tool_rv.data = [{"text": "No API tools found", "secondary_text": "Check server connection", "tool_data": {}, "bg_color": [1, 1, 1, 1]}]
        
        else:
            rv_data = []
            # 3. Create items
            for tool_obj in all_tools:
                rv_data.append({
                    "text": f"{tool_obj['name']} (ID: {tool_obj['id']})",
                    "secondary_text": f"Status: {tool_obj['status']} | Available: {tool_obj['available_quantity']}",
                    "tool_data": tool_obj,
                    "bg_color": [1, 1, 1, 1]
                })

            # 4. Add "Other" Option to the bottom
            other_tool = {"id": 0, "name": "Other", "status": "Manual", "available_quantity": "-"}
            rv_data.append({
                "text": "Other / Not Listed",
                "secondary_text": "Select this if you can't find the tool",
                "tool_data": other_tool,
                "bg_color": [1, 1, 1, 1]
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
        
        # Visual feedback: highlight selected row in data model
        rv = self.ids.tool_recycle_view
        for i, item in enumerate(rv.data):
            if item.get('tool_data', {}).get('id') == tool_data.get('id'):
                rv.data[i]['bg_color'] = [0.86, 0.93, 1, 1]
            else:
                rv.data[i]['bg_color'] = [1, 1, 1, 1]
        
        rv.refresh_from_data()
        
    def proceed(self):
        """
        User clicked Next. Confirm this tool and save to transaction list.
        Compatible with both 'Camera Flow' and 'Dev Flow'.
        """
        if self.selected_tool and self.selected_tool['name'] == "Other":
            self.go_to('manual tool entry screen')
            return

        app = App.get_running_app()
        if hasattr(app, 'session') and app.session.transaction_type == "return":
            print("[UI] Guard: return flow cannot proceed via ToolSelectionScreen. Redirecting.")
            self.go_to('tool return selection screen')
            return

        app = App.get_running_app()
        if hasattr(app, 'session'):
            session = app.session

            # Ensure there is an active transaction for this correction flow.
            if not session.current_transaction:
                print("[UI] Dev Mode: Creating dummy transaction for manual selection.")

                from datetime import datetime

                now = datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                milliseconds = int(now.microsecond / 1000)
                timestamp_id = f"{timestamp}-{milliseconds:03d}"
                filename = f"{timestamp_id}.jpg"

                session.start_new_transaction(timestamp_id, filename)

            # Manual correction should keep classification as incorrect.
            session.set_classification_correct(False)

            # Replace predicted tool shown on ToolConfirm screen with user's selected tool.
            selected_name = self.selected_tool.get('name', 'Unknown Tool')
            session.identified_tool_data = {
                'prediction': selected_name,
                'score': 1.0,
            }

        # Return to ToolConfirm so scan-more/finish decisions happen in one place.
        self.go_to('tool confirm screen')
