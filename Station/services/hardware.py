import platform
import time
from kivy.event import EventDispatcher
from smartcard.System import readers
from smartcard.util import toHexString
from kivy.clock import Clock
from kivy.core.window import Window

# Import settings from your config.py
from config import (
    PIN_LOAD_CELL_DAT, PIN_LOAD_CELL_CLK,
    PIN_LED_GREEN, PIN_LED_RED, PIN_LED_YELLOW,
    LOAD_CELL_THRESHOLD
)

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
        
        # Load Cell State
        self.lgpio_handle = None
        self.stable_reads = 0
        self.offset = 382000  # From your calibration script
        self.STABLE_READS_REQUIRED = 3
        
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
        
        # Initialize load cell
        self._setup_load_cell()
        
        # Start checking for smart cards every .5 second
        print("[HARDWARE] Starting PC/SC Reader Polling...")
        Clock.schedule_interval(self._check_pcsc_reader, 0.5)
        
        # Start monitoring load cell every 0.1 seconds
        print("[HARDWARE] Starting Load Cell Monitoring...")
        Clock.schedule_interval(self._check_load_cell, 0.1)
        
    def _check_pcsc_reader(self, dt):
        try:
            # Get list of available readers
            r_list = readers()
            if not r_list:
                return # No reader plugged in
            
            reader = r_list[0] # Use the first reader found
            # print(f"Using: {reader=}")        # DEBUG
            connection = reader.createConnection()
            
            # Try to connect (fails if no card is on the reader)
            try:
                connection.connect()
                
                # Send ADPU command to get the UID (Standard for Mifare cards)
                # Command: FF CA 00 00 00 (Get Data)
                GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                data, sw1, sw2 = connection.transmit(GET_UID)
                
                if sw1 == 0x90: # Success code
                    # Convert raw bytes to a hex string (e.g., "04 A3 5E...")
                    uid_hex = toHexString(data).replace(" ", "")
                    print(f"[HARDWARE] PC/SC Card Detected: {uid_hex}")
                    
                    # Dispatch event
                    self.dispatch('on_card_scanned', uid_hex)
            except Exception:
                # No card present, just ignore
                # print("no card detected")     # DEBUG
                pass
        
        except Exception as e:
            print(f"Error polling reader: {e}")
    
    def _setup_load_cell(self):
        """Initialize HX711 load cell on GPIO pins"""
        try:
            import lgpio
            
            # HX711 wiring
            self.DOUT_PIN = 5   # DOUT → GPIO 5
            self.SCK_PIN  = 6   # SCK  → GPIO 6
            self.CHIP = 0       # /dev/gpiochip0
            
            # Detection parameters
            self.STABLE_READS = 3
            self.OBJECT_THRESHOLD = 1000  # minimum raw weight
            self.offset = 382000  # calibration offset
            
            # State tracking
            self.stable_count = 0
            self.object_detected = False
            self.detection_time = None
            
            # Setup GPIO
            self.gpio_handle = lgpio.gpiochip_open(self.CHIP)
            lgpio.gpio_claim_input(self.gpio_handle, self.DOUT_PIN)
            lgpio.gpio_claim_output(self.gpio_handle, self.SCK_PIN, 0)
            
            print("[HARDWARE] Load cell initialized")
        except Exception as e:
            print(f"[HARDWARE] Load cell init error: {e}")
            self.gpio_handle = None
    
    def _hx711_read_raw(self):
        """Read raw value from HX711"""
        import lgpio
        
        while lgpio.gpio_read(self.gpio_handle, self.DOUT_PIN) == 1:
            time.sleep(0.0001)
        
        value = 0
        for _ in range(24):
            lgpio.gpio_write(self.gpio_handle, self.SCK_PIN, 1)
            value = (value << 1) | lgpio.gpio_read(self.gpio_handle, self.DOUT_PIN)
            lgpio.gpio_write(self.gpio_handle, self.SCK_PIN, 0)
        
        lgpio.gpio_write(self.gpio_handle, self.SCK_PIN, 1)
        lgpio.gpio_write(self.gpio_handle, self.SCK_PIN, 0)
        
        if value & 0x800000:
            value -= 1 << 24
        
        return value
    
    def _get_raw_weight(self):
        """Get calibrated weight reading"""
        return self._hx711_read_raw() - self.offset
    
    def _check_load_cell(self, dt):
        """Poll load cell and dispatch event after 2-second delay"""
        if not hasattr(self, 'gpio_handle') or self.gpio_handle is None:
            return
        
        try:
            weight = self._get_raw_weight()
            
            # Object detected logic
            if weight > self.OBJECT_THRESHOLD:
                self.stable_count += 1
                
                # Once stable reads achieved, start timer
                if self.stable_count >= self.STABLE_READS and not self.object_detected:
                    self.object_detected = True
                    self.detection_time = time.time()
                    print(f"[HARDWARE] Object detected! Weight: {weight:.0f}. Waiting 2 seconds...")
                
                # Check if 2 seconds have passed since detection
                if self.object_detected and self.detection_time:
                    elapsed = time.time() - self.detection_time
                    if elapsed >= 2.0:
                        print(f"[HARDWARE] 2 seconds elapsed. Triggering camera!")
                        self.dispatch('on_load_cell_detect', weight)
                        # Reset detection state
                        self.object_detected = False
                        self.detection_time = None
                        self.stable_count = 0
            else:
                # Object removed or not present
                if self.object_detected:
                    print("[HARDWARE] Object removed before 2 seconds")
                self.stable_count = 0
                self.object_detected = False
                self.detection_time = None
                
        except Exception as e:
            print(f"[HARDWARE] Load cell read error: {e}")
    
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
            self.dispatch('on_card_scanned', "10131867")
                
