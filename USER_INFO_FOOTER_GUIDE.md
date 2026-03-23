# User Info Footer Implementation Guide

## Overview
A persistent footer component has been added to display user information across all screens. When a user logs in via UCID verification, their data (first_name, ucid, email) is automatically displayed at the bottom of every screen.

## How It Works

### Components Created

1. **UserInfoFooter Component** (`View/components/user_info_footer.py` & `.kv`)
   - Displays user name, UCID, and email
   - Shows transaction type (BORROW/RETURN) with color coding
   - Automatically binds to SessionManager for live updates
   - Red background for "borrow", Green for "return"

2. **Updated BaseScreen** (`View/baseScreen.py`)
   - Now imports UserInfoFooter for reference

### Data Flow

```
APIClient.validate_user()
    ↓
Returns: {'first_name': '...', 'ucid': '...', 'email': '...'}
    ↓
WelcomeScreen stores data in: app.session.user_data
    ↓
UserInfoFooter automatically detects change and displays it
```

## How to Add Footer to Screens

### Simple 3-Step Process

1. **Update your screen's KV file:**
   - Change the main `MDBoxLayout` from padding/spacing to use a nested structure
   - Add `UserInfoFooter` at the bottom

2. **Example:**

```kv
<YourScreen>:
    md_bg_color: 1, 1, 1, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "0dp"
        spacing: "0dp"

        MDBoxLayout:
            orientation: 'vertical'
            padding: "20dp"      # Your original padding
            spacing: "20dp"      # Your original spacing

            # All your existing content goes here
            # Make sure size_hint_y values don't exceed 0.95

            Widget:
                size_hint_y: 0.5

            MDLabel:
                text: "Your Content"
                size_hint_y: 0.4

        # Add this footer at the bottom
        UserInfoFooter:
            size_hint_y: None
            height: "60dp"
```

### Key Points

- The outer `MDBoxLayout` has `padding: "0dp"` and `spacing: "0dp"`
- Your content goes in the inner `MDBoxLayout` with your preferred padding/spacing
- `UserInfoFooter` must have `size_hint_y: None` and `height: "60dp"`
- Inner content's `size_hint_y` values should total < 0.95 (leaving room for footer)

## Screens to Update

Apply the footer to all transaction screens:
- [ ] WelcomeScreen (optional - footer shows "Guest")
- [ ] ActionSelectionScreen
- [ ] CaptureScreen ✓ (already done)
- [ ] ToolConfirmScreen
- [ ] ToolSelectionScreen
- [ ] TransactionConfirmScreen
- [ ] CheckoutConfirmationScreen
- [ ] ManualEntryScreen
- [ ] UserErrorScreen

## What UserInfoFooter Displays

### When User is Logged In
```
John Doe                                    [BORROW]
30012345 | john.doe@university.edu
```

### When No User (on Welcome screen or after logout)
```
Guest                                       [------]
-- | --
```

### Colors
- **BORROW**: Red background (#C21315)
- **RETURN**: Green background (#339933)

## Important: Session Data Structure

Make sure `app.session.user_data` is set when user validates successfully in WelcomeScreen:

```python
# In validate_user_async/handle_validation_result:
if result['success']:
    app.session.user_data = result['data']  # Contains: first_name, ucid, email
    app.session.user_id = result['data']['ucid']
```

## Customization

### Change Footer Height
In any screen's KV file, modify:
```kv
UserInfoFooter:
    height: "80dp"  # Change to your preferred height
```

### Change Footer Colors
In `user_info_footer.py`, modify the RGB values in `on_transaction_type_change()`:
```python
if transaction_type.lower() == 'return':
    self.transaction_color = [0.2, 0.6, 0.2, 1]  # Adjust RGB
else:
    self.transaction_color = [0.76, 0.19, 0.20, 1]  # Adjust RGB
```

### Change Footer Layout
Edit `View/components/user_info_footer.kv` to modify the layout, labels, or styling.

## Testing

1. Run the app and scan/enter a UCID
2. Footer should appear at the bottom of every screen with user data
3. Change transaction type (borrow↔return)
4. Footer background color should change dynamically
5. Logout/Cancel should reset footer to "Guest"

## Files Modified

- ✓ `/Station/View/baseScreen.py` - Added import
- ✓ `/Station/View/CaptureScreen/capture_screen.kv` - Added footer
- ✓ `/Station/main.py` - Added UserInfoFooter import

## Files Created

- ✓ `/Station/View/components/user_info_footer.py` - Component class
- ✓ `/Station/View/components/user_info_footer.kv` - UI layout
- ✓ `/Station/View/FOOTER_TEMPLATE.txt` - Quick reference template
