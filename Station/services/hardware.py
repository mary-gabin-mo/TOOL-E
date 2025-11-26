import platform
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.core.window import Window

# Check system type
IS_PI = platform.machine() in ("aarch64", "armv7l")

class HardwareManager(EventDispatcher):
    """
    The central hub for all hardware interactions.
    Dispatches events that Screens can listen to.
    """
    
    # Define custome events that the UI can listen for
    __events__ = ('on_load_cell_detect', 'on_card_scanned')
    
    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.is_pi = IS_PI
        
        if self.is_pi:
            self._setup_real_hardware()
        else:
            self._setup_mock_hardware()
            
    # --- Event Stubs (required by Kivy) ---
    def on_load_cell_detect(self, weight):
        """Called when load cell detects an object > threshold"""
        pass
    
    def on_card_scanned(self, card_id):
        """Called when a UNICARD is tapped"""
        pass
    
    # --- REAL HARDWARE (Raspberry Pi) ---
    def _setup_real_hardware(self):
        print("[HARDWARE] Initializing Real Pi Hardware...")
        
        # implement GPIO setup...
        # implement other methods for the real hardware
        barcode = "#barcode_test#" ### Replace with the card reader input
        self.dispatch('on_card_scanned', barcode)
    
    # --- MOCK HARDWARE (Mac/Windows) ---
    def _setup_mock_hardware(self):
        print("[HARDWARE] Initializing MOCK Hardware (Dev Mode)...")
        print("   -> Press 'd' to simulate Load Cell Trigger")
        print("   -> Press 'c' to simulate Card Scan")
        
        # Bind keyboard keys to simulate hardware events
        Window.bind(on_key_down=self._on_mock_keyboard_input)
        
    def _on_mock_keyboard_input(self, window, key, scancode, codepoint, modifiers):
        # 'd' key (100) simulates Load Cell
        if key == 100: 
            print("[MOCK] Load Cell Triggered!")
            self.dispatch('on_load_cell_detect', weight=500.0)
        
        # 'c' key (99) simulates Card Tap
        elif key == 99: 
            print("[MOCK] Card Scanned!")
            self.dispatch('on_card_scanned', "##### barcode_dev #####")
                