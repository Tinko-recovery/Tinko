import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from app.models import Organization
    print("Import successful!")
except NameError as e:
    print(f"NameError: {e}")
except Exception as e:
    print(f"Error: {e}")
