from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ObjectProperty, ListProperty

class SessionManager(EventDispatcher):
    """
    Holds the state of the current transaction.
    Accessible from any scree via App.get_running_app().session
    """
    
    # Kivy Properties allow the UI to automatically update if these change
    
    # 'borrow' or 'return'
    transation_type = StringProperty("borrow")
    
    # # The User ID (e.g. "30012345")
    # user_id = StringProperty(None, allownone=True)
    
    # Full user details from DB (Name, Photo URL, etc.)
    user_data = ObjectProperty(None, allownone=True)
    
    # List of tools scanned in this session
    # e.g. [{'name': 'Hammer', 'id': 1}, {'name': 'Wrench', 'id': 2}]
    scanned_tools = ListProperty([])
    
    def reset(self):
        """Clear data for the next user."""
        print("[SESSION] Resetting settion state...")
        self.transaction_type = "borrow" # Default
        self.user_id = None
        self.user_data = None
        self.scanned_tools = []
        
    def set_transaction_type(self, type_str):
        if type_str.lower() not in ['borrow', 'return']:
            print(f"[ERROR] Invalid transaction type: {type_str}")
            return
        self.transaction_type = type_str.lower()
        print(f"[SESSION] Transaction Type set to: {self.transaction_type}")
        
    def add_tool(self, tool_data):
        self.scanned_tools.append(tool_data)
        print(f"[SESSION] Added tool: {tool_data.get('name', 'Unknown')}")
        
        