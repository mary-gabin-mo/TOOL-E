import platform
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
        print("[HARDWARE] Initializing Real Pi Hardware (LGPIO)...")
        
        try:
            import lgpio
            
            # 1. Open GPIO Chip (usually 0 on Pi 5)
            self.lgpio_handle = lgpio.gpiochip_open(0)
            
            # 2. Setup Load Cell Pins
            lgpio.gpio_claim_input(self.lgpio_handle, PIN_LOAD_CELL_DAT)
            lgpio.gpio_claim_output(self.lgpio_handle, PIN_LOAD_CELL_CLK, 0)
            
            # 3. Setup LEDs (Claiming them for output)
            lgpio.gpio_claim_output(self.lgpio_handle, PIN_LED_GREEN, 0)
            lgpio.gpio_claim_output(self.lgpio_handle, PIN_LED_RED, 0)
            lgpio.gpio_claim_output(self.lgpio_handle, PIN_LED_YELLOW, 0)
            
            # Turn on Yellow (Idle) initially
            self.set_leds('idle')

            # 4. Start polling the load cell 
            # Run 10 times a second (0.1s interval)
            Clock.schedule_interval(self._poll_load_cell, 0.1)

        except ImportError:
            print("[ERROR] lgpio not found. Hardware control disabled.")
        except Exception as e:
            print(f"[ERROR] GPIO Setup failed: {e}")
        
        # implement GPIO setup...
        # implement other methods for the real hardware
        barcode = "#barcode_test#" ### Replace with the card reader input
        self.dispatch('on_card_scanned', barcode)
        
        # # Start checking for smart cards every .5 second
        print("[HARDWARE] Starting PC/SC Reader Polling...")
        Clock.schedule_interval(self._check_pcsc_reader, 0.5)
        
    def _read_hx711_raw(self):
        """
        Bit-banging logic to read from HX711 using lgpio.
        Ported from your provided script.
        """
        import lgpio
        import time
        
        # Wait for DOUT to go low (ready)
        # Timeout loop to prevent UI freezing if sensor is disconnected
        timeout = 0
        while lgpio.gpio_read(self.lgpio_handle, PIN_LOAD_CELL_DAT) == 1:
            time.sleep(0.0001)
            timeout += 1
            if timeout > 1000: # approx 0.1s timeout
                return None

        value = 0
        # Pulse clock 24 times to read data
        for _ in range(24):
            lgpio.gpio_write(self.lgpio_handle, PIN_LOAD_CELL_CLK, 1)
            value = (value << 1) | lgpio.gpio_read(self.lgpio_handle, PIN_LOAD_CELL_DAT)
            lgpio.gpio_write(self.lgpio_handle, PIN_LOAD_CELL_CLK, 0)

        # Pulse clock 1 more time to set gain to 128 (standard)
        lgpio.gpio_write(self.lgpio_handle, PIN_LOAD_CELL_CLK, 1)
        lgpio.gpio_write(self.lgpio_handle, PIN_LOAD_CELL_CLK, 0)

        # Convert 24-bit 2's complement to signed int
        if value & 0x800000:
            value -= 1 << 24

        return value    
    
    def _poll_load_cell(self, dt):
        """
        Periodically checks weight. Replaces 'wait_for_object' loop.
        """
        if not self.lgpio_handle:
            return

        raw_val = self._read_hx711_raw()
        if raw_val is None:
            return # Sensor not ready

        current_weight = raw_val - self.offset

        # Check Threshold
        if current_weight > LOAD_CELL_THRESHOLD:
            self.stable_reads += 1
        else:
            self.stable_reads = 0

        # Trigger Event
        if self.stable_reads >= self.STABLE_READS_REQUIRED:
            print(f"[HARDWARE] Object Detected! Weight: {current_weight}")
            self.dispatch('on_load_cell_detect', current_weight)
            # Reset stable reads so we don't trigger 30 times a second while object sits there
            # Or you can add logic to wait for removal before triggering again.
            self.stable_reads = -50 # Simple "debounce" delay
        
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
            
    def cleanup(self):
        """Release GPIO resources on app exit."""
        if self.lgpio_handle is not None:
            import lgpio
            lgpio.gpiochip_close(self.lgpio_handle)
            self.lgpio_handle = None
            print("[HARDWARE] GPIO handle closed.")
    
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
                
