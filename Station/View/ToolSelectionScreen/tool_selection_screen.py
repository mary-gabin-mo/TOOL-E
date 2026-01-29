from kivy.app import App
from kivymd.uix.list import OneLineListItem

from View.baseScreen import BaseScreen

class ToolSelectionScreen(BaseScreen):
    
    def on_enter (self):
        """Called every time the screen is displayed."""
        self.populate_list()
        
    def populate_list(self):
        """Clears the list and re-adds tool items using full data objects."""
        # 1. Clear previous items so we don't duplicate
        scroll_list = self.ids.tool_list_container
        scroll_list.clear_widgets()
        
        # 2. Mock data (Replace with API data later)
        # Structure: List of Dictionaries
        all_tools = [
            {"id": 1, "name": "Hammer", "available": 0, "inventory": 1},
            {"id": 2, "name": "Tape Measure", "available": 1, "inventory": 1},
            {"id": 3, "name": "Screwdriver", "available": 2, "inventory": 2},
            {"id": 4, "name": "Breadboard", "available": 1, "inventory": 2},
            # ... etc
        ]
        
        # 3. Create items
        for tool_obj in all_tools:
            # only display the name
            item = OneLineListItem(text=tool_obj['name'])
            
            # bind the click event
            # use a lambda to pass the specific tool name to the function
            item.bind(on_release=lambda x, t=tool_obj: self.on_tool_selected(t))
            
            # Add to the scroll view
            scroll_list.add_widget(item)
            
    def on_tool_selected(self, tool_data):
        """
        Receives the full tool dictionary (e.g., {"id": 1, "name": "Hammer", "available": 0, "inventory": 1})
        """
        print(f"[UI] User manually selected: {tool_data.get('name')} (ID: {tool_data.get('id')})")
        
        # 1. Update Session
        app = App.get_running_app()
        
        if hasattr(app, 'session'):
            # Session stores the full object containing the ID
            app.session.add_tool(tool_data)
                    
        # 2. navigate to Confirmation Screen
        # self.go_to('confirm_screen')