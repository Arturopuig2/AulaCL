import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def debug_unlock():
    # 1. Login to get token
    print("Logging in...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", data={"username": "arturo", "password": "password123"})
        # Note: assuming password is 'password123' based on previous context or common dev passwords, 
        # BUT wait, the user created the account. 
        # I will try to login as 'admin' first since I know that credential '1234'.
        # Actually, let's just use the Admin token to test the endpoint, logic is the same (User model).
        if resp.status_code != 200:
             # Fallback to admin if arturo fails (maybe password diff)
             resp = requests.post(f"{BASE_URL}/auth/token", data={"username": "admin", "password": "1234"})
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    if resp.status_code != 200:
        print(f"Login Failed: {resp.status_code} {resp.text}")
        return

    token = resp.json().get("access_token")
    print(f"Got Token: {token[:10]}...")

    # 2. Try Unlock with Valid Code
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"access_code": "ZFXD8WGL"}
    
    print(f"Sending Unlock Request: {payload}")
    try:
        unlock_resp = requests.post(f"{BASE_URL}/auth/unlock", json=payload, headers=headers)
        print("--- RESPONSE ---")
        print(f"Status Code: {unlock_resp.status_code}")
        print(f"Body: {unlock_resp.text}")
        print("----------------")
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    debug_unlock()
