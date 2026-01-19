from View.WelcomeScreen.welcome_screen import WelcomeScreen
from View.ActionSelectionScreen.action_selection_screen import ActionSelectionScreen
from View.CaptureScreen.capture_screen import CaptureScreen
from View.ManualEntryScreen.manual_entry_screen import ManualEntryScreen
from View.ToolConfirmScreen.tool_confirm_screen import ToolConfirmScreen
from View.ToolSelectionScreen.tool_select_screen import ToolSelectScreen
from View.UserErrorScreen.user_error_screen import UserErrorScreen

screens = {
    "welcome screen": {
        "view": WelcomeScreen
    },
    "manual entry screen": {
        "view": ManualEntryScreen
    },
    "action selection screen": {
        "view": ActionSelectionScreen
    },
    "capture screen": {
        "view": CaptureScreen
    },
    "tool confirm screen": {
        "view": ToolConfirmScreen
    },
    "tool select screen": {
        "view": ToolSelectScreen
    },
    "user error screen": {
        "view": UserErrorScreen
    },
}