import requests
import os
import json
from datetime import datetime
from kivy.event import EventDispatcher

# Import settings from the config file
from config import (
    API_VALIDATE_USER,
    API_IDENTIFY_TOOL,
    API_TRANSACTION,
    API_GET_TOOLS,
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
            payload = {"barcode": None, "UCID": ucid} # Distinguish whether it's barcode or UCID in the server with regex
        
        else: # barcode is alphanumeric
            barcode = id;
            print(f"[API] Validating User: {barcode=}...")
            payload = {"barcode": barcode, "UCID": None} # Distinguish whether it's barcode or UCID in the server with regex
            
        try:
            response = requests.post(
                API_VALIDATE_USER,
                json=payload,
                timeout=NETWORK_TIMEOUT
            )
            response.raise_for_status() # Raise error for 4xx/5xx codes
            
            # Success!
            res = response.json()
            print(f"{res=}")
            if res.get('success'): 
                print(f"[API] Success: {res}")
                return res
            else:
                print(f"[API] Waiver Expired Error: {res.get('message')}")
                return {'success': False, 'error': res.get('message')}
        
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
        
    def get_tools(self):
        """
        Get all tools from the database.
        
        Returns:
            list: List of tool dictionaries
        """
        print("[API] Fetching all tools...")
        try:
            response = requests.get(
                API_GET_TOOLS,
                timeout=NETWORK_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"[API] Error fetching tools: {e}")
            return []

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
                # Value is a tuple: (filename, file_object, content_type)
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
                f"{API_TRANSACTION}/kiosk",
                json=transaction_data,
                timeout=NETWORK_TIMEOUT
            )
            response.raise_for_status()
            
            print("[API] Transaction Recorded Successfully.")
            return {'success': True}
        
        except Exception as e:
            print(f"[API] Transaction Failed: {e}")
            return {'success': False, 'error': "Could not record transaction."}
    
    def return_tools(self, transactions):
        """
        Mark tools as returned. 
        Args:
           transactions (list): List of dicts, each with 'transaction_id'.
        """
        print(f"[API] Returning {len(transactions)} tools...")
        success_count = 0
        errors = []
        
        current_time = datetime.now().isoformat()
        
        for tx in transactions:
            tx_id = tx.get('transaction_id')
            if not tx_id:
                errors.append(f"Missing transaction_id for tool: {tx}")
                continue
                
            payload = {
                "return_timestamp": current_time
            }
            
            try:
                # Update the transaction
                # API_TRANSACTION endpoint is base_url/transactions
                response = requests.put(
                    f"{API_TRANSACTION}/{tx_id}",
                    json=payload,
                    timeout=NETWORK_TIMEOUT
                )
                response.raise_for_status()
                print(f"[API] Successfully returned transaction {tx_id}")
                success_count += 1
            except Exception as e:
                print(f"[API] Failed to return transaction {tx_id}: {e}")
                errors.append(f"Failed to return transaction {tx_id}: {e}")
                
        if success_count > 0:
            return {'success': True, 'count': success_count, 'errors': errors}
        else:
            return {'success': False, 'error': f"No tools returned. Errors: {errors}"}

    def get_user_unreturned_tools(self, user_id):
        """
        Fetch all unreturned tools for a specific user.
        
        Args:
            user_id (str): The user's UCID
            
        Returns:
            dict: {'success': True, 'data': [tool_list]} OR {'success': False, 'error': str}
        """
        print(f"[API] Fetching unreturned tools for user: {user_id}")
        
        try:
            # Try current route first, then legacy query route used by some backend versions.
            candidate_calls = [
                (f"{API_TRANSACTION}/user/{user_id}/unreturned", None),
                (f"{API_TRANSACTION}/unreturned", {"user_id": user_id}),
            ]

            last_error = None
            payload = None

            for url, params in candidate_calls:
                try:
                    response = requests.get(url, params=params, timeout=NETWORK_TIMEOUT)
                    response.raise_for_status()
                    payload = response.json()
                    break
                except Exception as e:
                    last_error = e

            if payload is None:
                raise last_error or Exception("No response from unreturned-tools endpoint")

            # Normalize backend response into a list for UI code.
            if isinstance(payload, list):
                tools = payload
            elif isinstance(payload, dict):
                tools = (
                    payload.get("data")
                    or payload.get("items")
                    or payload.get("tools")
                    or payload.get("unreturned_tools")
                    or []
                )
            else:
                tools = []

            if not isinstance(tools, list):
                tools = []

            print(f"[API] Found {len(tools)} unreturned tools")
            return {'success': True, 'data': tools}

        except Exception as e:
            print(f"[API] Error fetching unreturned tools: {e}")
            return {'success': False, 'error': str(e)}