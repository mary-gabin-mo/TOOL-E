import os

# --- NETWORK SETTINGS ---
# The IP address of your FastAPI Server (PC)
# Use "localhost" for testing on Mac, or the actual IP (e.g., "192.168.1.10") for Pi
SERVER_IP = "192.168.1.21" 
SERVER_PORT = 5000
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# API Endpoints
API_VALIDATE_USER = f"{BASE_URL}/validate_user"
API_IDENTIFY_TOOL = f"{BASE_URL}/identify_tool"
API_TRANSACTION   = f"{BASE_URL}/transaction"
API_GET_TOOLS     = f"{BASE_URL}/tools"

# Timeouts (in seconds)
NETWORK_TIMEOUT = 5.0


# --- HARDWARE SETTINGS --- ##### NEED #####
# GPIO Pins (BCM Numbering)
PIN_LOAD_CELL_DAT = 5
PIN_LOAD_CELL_CLK = 6
PIN_LED_GREEN     = 17
PIN_LED_RED       = 27
PIN_LED_YELLOW    = 22

# Load Cell Calibration
LOAD_CELL_THRESHOLD = 20.0  # Minimum weight (grams) to trigger "Tool Detected"
LOAD_CELL_DEBOUNCE  = 2.0   # Seconds weight must be stable


# --- UI SETTINGS ---
# Paths
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
LOGO_PATH  = os.path.join(ASSETS_DIR, '/images/logo_black.png')
FONT_PATH  = os.path.join(ASSETS_DIR, 'fonts')

# # Camera ##### NEED #####
# # Resolution for the "Live Feed" preview (keep low for performance)
# CAMERA_PREVIEW_RES = (640, 480)
# # Resolution for the actual recognition image (higher quality)
# CAMERA_CAPTURE_RES = (1920, 1080)