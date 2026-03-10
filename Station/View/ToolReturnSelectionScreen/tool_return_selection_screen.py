from kivy.app import App
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.selectioncontrol import MDCheckbox
from View.baseScreen import BaseScreen

class ToolReturnSelectionScreen(BaseScreen):
    
    def on_enter(self):
        """
        Populate the list with non-returned tools.
        Filter by tool type if the scanned tool was confirmed correct.
        """
        app = App.get_running_app()
        
        # Get the predicted tool name from the current transaction
        predicted_tool = None
        tool_was_confirmed = getattr(app.session, 'tool_was_confirmed', False)
        
        if hasattr(app.session, 'identified_tool_data') and app.session.identified_tool_data:
            predicted_tool = app.session.identified_tool_data.get('prediction', None)
        
        # Clear existing list
        list_container = self.ids.tool_list_container
        list_container.clear_widgets()
        
        # Get non-returned tools for this user from API
        # For now, we'll use a placeholder - you'll need to implement the API call
        non_returned_tools = self._fetch_non_returned_tools()
        
        print(f"[DEBUG] Fetched {len(non_returned_tools)} tools")
        print(f"[DEBUG] First tool data: {non_returned_tools[0] if non_returned_tools else 'None'}")
        print(f"[DEBUG] Type of first tool: {type(non_returned_tools[0]) if non_returned_tools else 'None'}")
        
        # Filter tools if the scanned tool was confirmed correct
        if tool_was_confirmed and predicted_tool:
            # Show only tools matching the predicted type
            filtered_tools = [tool for tool in non_returned_tools if isinstance(tool, dict) and tool.get('tool_name') == predicted_tool]
            self.ids.title_label.text = f"Select {predicted_tool} to Return"
        else:
            # Show all non-returned tools
            filtered_tools = [tool for tool in non_returned_tools if isinstance(tool, dict)]
            self.ids.title_label.text = "Select Tool to Return"
        
        # Display filtered tools
        if not filtered_tools:
            self.ids.empty_message.opacity = 1
            self.ids.empty_message.text = "No unreturned tools found"
            self.ids.continue_btn.disabled = True
        else:
            self.ids.empty_message.opacity = 0
            
            for tool in filtered_tools:
                try:
                    # Create list item with checkbox
                    item = TwoLineAvatarIconListItem(
                        text=tool.get('tool_name', 'Unknown Tool'),
                        secondary_text=f"Borrowed: {tool.get('borrow_date', 'N/A')} • Due: {tool.get('due_date', 'N/A')}",
                    )
                    
                    # Add checkbox
                    checkbox = MDCheckbox(
                        size_hint=(None, None),
                        size=("48dp", "48dp"),
                    )
                    checkbox.tool_id = tool.get('tool_id', 0)  # Store tool ID for later
                    checkbox.bind(active=self.on_checkbox_change)
                    
                    item.add_widget(checkbox)
                    list_container.add_widget(item)
                except Exception as e:
                    print(f"[ERROR] Failed to create list item for tool: {tool}, Error: {e}")
    
    def _fetch_non_returned_tools(self):
        """
        Fetch non-returned tools for the current user from the API.
        Returns a list of dictionaries with tool information.
        """
        app = App.get_running_app()
        
        # Get user ID from session
        user_id = None
        if hasattr(app.session, 'user_data') and app.session.user_data:
            user_id = app.session.user_data.get('ucid') or app.session.user_data.get('id')
        
        if not user_id:
            print("[ERROR] No user ID found in session")
            return []
        
        # Call API to get non-returned tools
        try:
            response = app.api_client.get_user_unreturned_tools(user_id)
            if response.get('success'):
                return response.get('data', [])
            else:
                print(f"[ERROR] Failed to fetch unreturned tools: {response.get('error')}")
                return []
        except Exception as e:
            print(f"[ERROR] Exception fetching unreturned tools: {e}")
            # Return mock data for testing
            return [
                {
                    'tool_id': 1,
                    'tool_name': 'Hammer',
                    'borrow_date': '2026-02-15',
                    'due_date': '2026-03-15'
                },
                {
                    'tool_id': 2,
                    'tool_name': 'Hammer',
                    'borrow_date': '2026-02-20',
                    'due_date': '2026-03-20'
                },
                {
                    'tool_id': 3,
                    'tool_name': 'Screwdriver',
                    'borrow_date': '2026-02-25',
                    'due_date': '2026-03-25'
                }
            ]
    
    def on_checkbox_change(self, checkbox, value):
        """Enable continue button if at least one tool is selected."""
        app = App.get_running_app()
        
        # Check if any checkboxes are selected
        list_container = self.ids.tool_list_container
        any_selected = False
        
        for item in list_container.children:
            for widget in item.children:
                if isinstance(widget, MDCheckbox) and widget.active:
                    any_selected = True
                    break
            if any_selected:
                break
        
        self.ids.continue_btn.disabled = not any_selected
    
    def confirm_selection(self):
        """
        Collect selected tools and add to session, then navigate to confirmation.
        """
        app = App.get_running_app()
        
        # Collect selected tool IDs
        list_container = self.ids.tool_list_container
        selected_tools = []
        
        for item in list_container.children:
            for widget in item.children:
                if isinstance(widget, MDCheckbox) and widget.active:
                    # Get the tool info
                    tool_id = widget.tool_id
                    tool_name = item.text
                    selected_tools.append({
                        'tool_id': tool_id,
                        'tool_name': tool_name
                    })
        
        # Add selected tools to session transactions
        for tool in selected_tools:
            app.session.confirm_current_tool(tool['tool_name'])
        
        print(f"[UI] Selected {len(selected_tools)} tools for return")
        
        # Navigate to return confirmation screen
        self.go_to('return confirmation screen')
    
    def go_back(self):
        """Return to tool confirmation screen."""
        self.go_to('tool confirm screen')
