from dotenv import load_dotenv
import os

# Load from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_path)

print("🔧 Loaded .env from:", env_path)
