from kivy.app import App
from kivymd.uix.list import TwoLineAvatarIconListItem, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from View.baseScreen import BaseScreen


class RightCheckbox(IRightBodyTouch, MDCheckbox):
    """Checkbox that behaves correctly inside MDList item right-side body."""
    pass

class ToolReturnSelectionScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._checkboxes = []
    
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
        self._checkboxes = []
        
        # Get non-returned tools for this user from API
        # For now, we'll use a placeholder - you'll need to implement the API call
        non_returned_tools = self._fetch_non_returned_tools()
        
        print(f"[DEBUG] Fetched {len(non_returned_tools)} tools")
        first_tool = non_returned_tools[0] if isinstance(non_returned_tools, list) and non_returned_tools else None
        print(f"[DEBUG] First tool data: {first_tool}")
        print(f"[DEBUG] Type of first tool: {type(first_tool) if first_tool is not None else 'None'}")
        
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
                    borrow_date = tool.get('borrow_date') or tool.get('checkout_timestamp') or 'N/A'
                    due_date = tool.get('due_date') or tool.get('desired_return_date') or 'N/A'
                    tool_name = tool.get('tool_name') or 'Unknown Tool'
                    item = TwoLineAvatarIconListItem(
                        text=tool_name,
                        secondary_text=f"Borrowed: {borrow_date} • Due: {due_date}",
                    )
                    
                    # Add checkbox
                    checkbox = RightCheckbox(
                        size_hint=(None, None),
                        size=("48dp", "48dp"),
                    )
                    checkbox.tool_id = tool.get('tool_id', 0)
                    checkbox.transaction_id = tool.get('transaction_id')
                    checkbox.tool_name = tool_name
                    checkbox.bind(active=self.on_checkbox_change)
                    self._checkboxes.append(checkbox)

                    # Make the full row tappable so users can select items reliably.
                    item.bind(on_release=lambda _item, cb=checkbox: setattr(cb, 'active', not cb.active))
                    
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
        any_selected = any(cb.active for cb in self._checkboxes)
        self.ids.continue_btn.disabled = not any_selected
    
    def confirm_selection(self):
        """
        Collect selected tools, store them in session, then navigate to confirmation.
        """
        app = App.get_running_app()
        
        # Collect selected tool IDs directly from our tracking list
        selected_tools = []
        
        for checkbox in self._checkboxes:
            if checkbox.active:
                selected_tools.append({
                    'transaction_id': getattr(checkbox, 'transaction_id', None),
                    'tool_id': getattr(checkbox, 'tool_id', None),
                    'tool_name': getattr(checkbox, 'tool_name', "Unknown Tool")
                })
        
        if not selected_tools:
            print("[UI] No tools selected.")
            return

        print(f"[UI] Selected {len(selected_tools)} tools for return")
        
        # Call API to process returns
        try:
            # Mark tools as returned in the backend
            result = app.api_client.return_tools(selected_tools)
            
            if result.get('success') or result.get('count', 0) > 0:
                # Store processed transactions in session so confirmation screen can show them
                app.session.transactions = selected_tools
                
                # Navigate to return confirmation screen
                self.go_to('return confirmation screen')
            else:
                print(f"[ERROR] Failed to return tools: {result.get('error')}")
                # You might want to show an error dialog here
        
        except Exception as e:
            print(f"[ERROR] Exception processing return: {e}")
            # Fallback for now if API fails (e.g. testing without backend)
            app.session.transactions = selected_tools
            self.go_to('return confirmation screen')
    
    def go_back(self):
        """Return to tool confirmation screen."""
        self.go_to('tool confirm screen')
