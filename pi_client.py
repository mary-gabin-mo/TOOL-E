import requests
import json
import time

DESKTOP_IP = "(desktop)"
DESKTOP_API_URL = f'http://{DESKTOP_IP}:5000/api/ingest'
DATA_FILE_PATH = 'data.json'

def send_data():
    try:
        with open(DATA_FILE_PATH, 'r') as f:
            data_to_send = json.load(f)
        
        print(f"--- Sending Data to Desktop ---")
        print(json.dumps(data_to_send, indent=4))

        # Send data
        response = requests.post(DESKTOP_API_URL, json=data_to_send, timeout=15)
        response.raise_for_status()

        #print server response
        server_response = response.json()
        print("\n Data Sent")
        print(f"Status: {server_response.get('status')}")
        print(f"Verification Check Passed: {server_response.get('verification_result)')}")

    except FileNotFoundError:
        print(f"Error: {DATA_FILE_PATH} not found")
    except requests.exceptions.RequestException as e:
        print(f"Connection/Request Error: Unable to connect to server at {DESKTOP_API_URL}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in data.json")

if __name__ == "__main__":
    send_data()
    