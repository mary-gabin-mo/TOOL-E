from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ObjectProperty, ListProperty, DictProperty

class SessionManager(EventDispatcher):
    """
    Holds the state of the current transaction.
    Accessible from any scree via App.get_running_app().session
    """
    
    # Kivy Properties allow the UI to automatically update if these change
    
    # 'borrow' or 'return'
    transaction_type = StringProperty("borrow")
    
    # # The User ID (e.g. "30012345")
    # user_id = StringProperty(None, allownone=True)
    
    # Full user details from DB (Name, Photo URL, etc.)
    user_data = ObjectProperty(None, allownone=True)
    
    # List of COMPLETED transactions for this session
    # Each item: {'transaction_id': '...', 'img_filename': '...', 'tool_name': '...'}
    transactions = ListProperty([])

    # The current transaction being processed (waiting for tool confirmation)
    current_transaction = DictProperty({})
    
    def reset(self):
        """Clear data for the next user."""
        print("[SESSION] Resetting settion state...")
        self.transaction_type = "borrow" # Default
        self.user_data = None
        self.transactions = []
        self.current_transaction = []
        
    def set_transaction_type(self, type_str):
        if type_str.lower() not in ['borrow', 'return']:
            print(f"[ERROR] Invalid transaction type: {type_str}")
            return
        self.transaction_type = type_str.lower()
        print(f"[SESSION] Transaction Type set to: {self.transaction_type}")
        
    def start_new_transaction(self, transaction_id, img_filename):
        """
        Called by Capture Screen immediately after taking a photo.
        Initializes a new pending transaction.
        """
        self.current_transaction = {
            "transaction_id": transaction_id,
            "img_filename": img_filename,
            "tool_name": None  # Will be filled after ML/User confirmation
        }
        print(f"[SESSION] Started Transaction: {transaction_id}")

    def confirm_current_tool(self, tool_name):
        """
        Called by Confirm Screen when user accepts the tool.
        Moves the data from 'current' to the permanent 'transactions' list.
        """
        if not self.current_transaction:
            print("[SESSION] Error: No active transaction to confirm.")
            return

        # Update the tool name
        self.current_transaction["tool_name"] = tool_name
        
        # Add to the main list
        self.transactions.append(dict(self.current_transaction))
        print(f"[SESSION] Confirmed Tool: {tool_name} (ID: {self.current_transaction['transaction_id']})")
        
        # Clear current
        self.current_transaction = {}
        
        