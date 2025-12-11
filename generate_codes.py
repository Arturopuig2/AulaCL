import requests
import argparse
import sys

# Configuration
API_URL = "http://127.0.0.1:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234" # Default password, could be passed as arg

def get_token():
    try:
        response = requests.post(f"{API_URL}/auth/token", data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Error getting admin token: {e}")
        print("Ensure the server is running and admin credentials are correct.")
        sys.exit(1)

def generate_codes(count):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{API_URL}/auth/admin/codes?count={count}", headers=headers)
        response.raise_for_status()
        codes = response.json()
        
        print(f"✅ Generated {len(codes)} new codes:")
        print("-" * 30)
        for code in codes:
            print(code)
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error generating codes: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Invitation Codes for Aula CL")
    parser.add_argument("count", type=int, nargs="?", default=1, help="Number of codes to generate")
    args = parser.parse_args()
    
    generate_codes(args.count)
