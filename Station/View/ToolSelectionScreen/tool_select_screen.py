from kivy.app import App
from kivymd.uix.list import OneLineListItem

from View.baseScreen import BaseScreen

class ToolSelectScreen(BaseScreen):
    
    def on_enter (self):
        """Called every time the screen is displayed."""
        self.populate_list()
        
    def populate_list(self):
        """Clears the list and re-adds tool items."""
        # 1. Clear previous items so we don't duplicate
        scroll_list = self.ids.tool_list_container
        scroll_list.clear_widgets()
        
        # 2. Mock data (Replace with API data later)
        tool_names = [
            "Hammer", "Screwdriver", "Wrench", "Pliers"
        ]
        
        # 3. Create items
        for name in tool_names:
            # Create the list item
            item = OneLineListItem(text=name)
            
            # bind the click event
            # use a lambda to pass the specific tool name to the function
            item.bind(on_release=lambda x, tool=name: self.on_tool_selected(tool))
            
            # Add to the scroll view
            scroll_list.add_widget(item)
            
    def on_tool_selected(self, tool_name):
        print(f"[UI] User manually selected: {tool_name}")
        
        # 1. Update Session
        app = App.get_running_app()
        
        # if hasattr(app, 'session'):
        app.session.selected_tool = tool_name
        
        # 2. navigate to Confirmation Screen
        # self.go_to('confirm_screen')