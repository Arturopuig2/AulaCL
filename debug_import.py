import sys
import os
sys.path.append(os.getcwd())

try:
    from app.auth import authenticate_user
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Other error: {e}")
