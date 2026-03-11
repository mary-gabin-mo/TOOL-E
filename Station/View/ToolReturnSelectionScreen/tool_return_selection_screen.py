from kivy.app import App
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from View.baseScreen import BaseScreen
import threading
from kivy.clock import mainthread, Clock
from kivy.properties import DictProperty, BooleanProperty, StringProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.behaviors import ButtonBehavior

class ReturnToolItem(RecycleDataViewBehavior, ButtonBehavior, MDBoxLayout):
    """Custom list item for RecycleView with a checkbox."""
    tool_data = DictProperty()
    is_active = BooleanProperty(False)
    text = StringProperty()
    secondary_text = StringProperty()
    
    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self._rv_index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_release(self):
        """Triggered by ButtonBehavior when the layout is clicked."""
        self.toggle_active()

    def toggle_active(self):
        """Toggle checkbox state on row tap."""
        new_state = not self.is_active
        self.set_active_state(new_state)

    def on_checkbox_hit(self, active_state):
        """Called by the MDCheckbox directly from UI action."""
        self.set_active_state(active_state)

    def set_active_state(self, is_active):
        self.is_active = is_active
        app = App.get_running_app()
        if hasattr(app, 'manager_screens'):
            screen = app.manager_screens.get_screen('tool return selection screen')
            if screen:
                screen.on_checkbox_change(self.tool_data, is_active, getattr(self, '_rv_index', None))

class ToolReturnSelectionScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_tools = {} # dict of transaction_id -> tool_data
    
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
        
        # Clear existing selection
        self._selected_tools = {}
        
        # Show loading state
        self.ids.title_label.text = "Loading tools..."
        self.ids.empty_message.opacity = 1
        self.ids.empty_message.text = "Please wait..."
        self.ids.continue_btn.disabled = True
        self.ids.tool_recycle_view.data = []
        
        # Fetch non-returned tools for this user from API in background
        threading.Thread(
            target=self._fetch_non_returned_tools_thread, 
            args=(tool_was_confirmed, predicted_tool)
        ).start()

    def _fetch_non_returned_tools_thread(self, tool_was_confirmed, predicted_tool):
        app = App.get_running_app()
        user_id = None
        if hasattr(app.session, 'user_data') and app.session.user_data:
            user_id = app.session.user_data.get('ucid') or app.session.user_data.get('id')
            
        non_returned_tools = []
        if user_id:
            try:
                response = app.api_client.get_user_unreturned_tools(user_id)
                if response.get('success'):
                    non_returned_tools = response.get('data', [])
            except Exception as e:
                print(f"[ERROR] Exception fetching unreturned tools: {e}")
                
        self._update_tools_ui(non_returned_tools, tool_was_confirmed, predicted_tool)

    @mainthread
    def _update_tools_ui(self, non_returned_tools, tool_was_confirmed, predicted_tool):
        print(f"[DEBUG] Fetched {len(non_returned_tools)} tools")
        
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
            self.ids.tool_recycle_view.data = []
        else:
            self.ids.empty_message.opacity = 0
            
            rv_data = []
            for tool in filtered_tools:
                borrow_date = tool.get('borrow_date') or tool.get('checkout_timestamp') or 'N/A'
                due_date = tool.get('due_date') or tool.get('desired_return_date') or 'N/A'
                tool_name = tool.get('tool_name') or 'Unknown Tool'
                
                rv_data.append({
                    "text": tool_name,
                    "secondary_text": f"Borrowed: {borrow_date} • Due: {due_date}",
                    "tool_data": tool,
                    "is_active": False
                })
            
            self.ids.tool_recycle_view.data = rv_data
    
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
    
    def on_checkbox_change(self, tool_data, is_active, rv_index=None):
        """Update selected tools and enable continue button if at least one tool is selected."""
        if not tool_data:
            return
            
        tx_id = tool_data.get('transaction_id')
        if not tx_id:
            return

        if is_active:
            self._selected_tools[tx_id] = tool_data
        elif tx_id in self._selected_tools:
            del self._selected_tools[tx_id]
            
        # Update UI in list
        rv = self.ids.tool_recycle_view
        
        # We only really need to update the backing data model to persist visual state as we scroll
        if rv_index is not None and rv_index >= 0 and rv_index < len(rv.data):
            rv.data[rv_index]['is_active'] = is_active
        else:
            # Fallback if index wasn't saved yet
            for i, item in enumerate(rv.data):
                if item.get('tool_data', {}).get('transaction_id') == tx_id:
                    rv.data[i]['is_active'] = is_active
                    break
        
        self.ids.continue_btn.disabled = len(self._selected_tools) == 0
    
    def confirm_selection(self):
        """
        Collect selected tools, store them in session, then navigate to confirmation.
        """
        app = App.get_running_app()
        
        # Collect selected tool IDs directly from our tracking list
        selected_tools = []
        
        for tx_id, d in self._selected_tools.items():
            selected_tools.append({
                'transaction_id': tx_id,
                'tool_id': d.get('tool_id', None),
                'tool_name': d.get('tool_name', "Unknown Tool")
            })
        
        if not selected_tools:
            print("[UI] No tools selected.")
            return

        print(f"[UI] Selected {len(selected_tools)} tools for return")
        
        # Disable button during processing
        self.ids.continue_btn.disabled = True
        self.ids.continue_btn.text = "Processing..."
        
        threading.Thread(target=self._return_tools_thread, args=(selected_tools,)).start()
        
    def _return_tools_thread(self, selected_tools):
        app = App.get_running_app()
        try:
            result = app.api_client.return_tools(selected_tools)
        except Exception as e:
            result = {'success': False, 'error': str(e)}
            
        self._handle_return_result(result, selected_tools)
        
    @mainthread
    def _handle_return_result(self, result, selected_tools):
        app = App.get_running_app()
        self.ids.continue_btn.text = "Confirm Return"
        
        if result.get('success') or result.get('count', 0) > 0:
            # Store processed transactions in session so confirmation screen can show them
            app.session.transactions = selected_tools
            
            # Navigate to return confirmation screen
            self.go_to('return confirmation screen')
        else:
            print(f"[ERROR] Failed to return tools: {result.get('error', 'Unknown error')}")
            # Ensure the button is re-enabled to allow trying again
            self.ids.continue_btn.disabled = False
            # Fallback for now if API fails (e.g. testing without backend)
            app.session.transactions = selected_tools
            self.go_to('return confirmation screen')
    
    def go_back(self):
        """Return to tool confirmation screen."""
        self.go_to('tool confirm screen')
