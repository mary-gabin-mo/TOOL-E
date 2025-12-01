import requests
import os
import json
from kivy.event import EventDispatcher

# Import settings from the config file
from config import (
    API_VALIDATE_USER,
    API_IDENTIFY_TOOL,
    API_TRANSACTION,
    NETWORK_TIMEOUT
)

class APIClient(EventDispatcher):
    """
    Handles all HTTP requests to the FastAPI Backend.
    """
    
    def validate_user(self, id):
        """
        Checks if a user exists and has a valid waiver.
        
        Args:
            id (str): The barcode from the card or UCID typed manually
            
        Returns:
            dict: {'success': True, 'data': user_dict} OR {'success': False, 'error': str}
        """
        
        # Determine if id is UCID or barcode
        if id.isdigit(): # if id contains digits only, it is UCID
            ucid = id;
            print(f"[API] Validating User: {ucid=}...")
            payload = {"barcode": null, "UCID": ucid} # Distinguish whether it's barcode or UCID in the server with regex
        
        else: # barcode is alphanumeric
            barcode = id;
            print(f"[API] Validating User: {barcode=}...")
            payload = {"barcode": barcode, "UCID": null} # Distinguish whether it's barcode or UCID in the server with regex
            
        try:
            response = requests.post(
                API_VALIDATE_USER,
                json=payload,
                timeout=NETWORK_TIMEOUT
            )
            response.raise_for_status() # Raise error for 4xx/5xx codes
            
            # Success!
            data = response.json()
            print(f"[API] Success: {data}")
            return {'success': True, 'data': data}
        
        except requests.exceptions.ConnectionError:
            print("[API] Connection Error: Is the server running?")
            return {'success': False, 'error': "Could not connect to server."}
        
        except requests.exceptions.Timeout:
            print("[API] Timeout Error")
            return {'success': False, 'error': "Server reuqest timed out."}
            
        except requests.exceptions.RequestException as e:
            # Handle 404 (User not found) - when user not found in the db
            if response and response.status_code == 404:
                return {'success': False, 'error': "User not found in database."}
            
            print(f"[API] Error: {e}")
            return {'success': False, 'error': f"System Error: {e}"}
        
    def upload_tool_image(self, image_path):
        """
        Uploads the captured image for recognition.
        
        Args:
            image_path(str): Full path to the .jpg file on the Pi.
        
        Returns:
            dict: {'sucess': True, 'tool': 'Hammer', 'conf': 0.98} OR Error dict
        """ 
        print(f"[API] Uploading image: {image_path}...")
        
        if not os.path.exists(image_path):
            return{'success': False, 'error': "Image file not found on disk."}
        
        try:
            # Open file in binary mode
            with open(image_path, 'rb') as img_file:
                # 'file' matches the parameter name in the FastAPI endpoint
                files = {'file': ('capture.jpg', img_file, 'image/jpeg')}
                
                response = requests.post(
                    API_IDENTIFY_TOOL,
                    files=files,
                    timeout=10.0 # Give images some more time than simple JSON
                )
                
            response.raise_for_status()
            data = response.json()
            
            print(f"[API] Recognition Result: {data}")
            return {'success': True, 'data': data}
        
        except Exception as e:
            print(f"[API] Upload Failed: {e}")
            return {'success': False, 'error': "Recognition failed. Please try again."}
        
        
    def submit_transaction(self, transaction_data):
        """
        Finalizes the Checkout or Return.
        
        Args:
            transaction_data (dict): {
                "user_id": "...",
                "tool_id": "...",
                "action": "borrow"|"return",
                ...
            }
        """
        print(f"[API] Submitting Transaction: {transaction_data}")
        
        try: 
            response = requests.post(
                API_TRANSACTION,
                json=transaction_data,
                timeout=NETWORK_TIMEOUT
            )
            response.raise_for_status()
            
            print("[API] Transaction Recorded Successfully.")
            return {'success': True}
        
        except Exception as e:
            print(f"[API] Transaction Failed: {e}")
            return {'success': False, 'error': "Could not record transaction."}