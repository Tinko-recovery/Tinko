import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ASK USER FOR PRODUCTION DB URL
print("Please paste your PRODUCTION Supabase Connection String:")
DATABASE_URL = input().strip()

if not DATABASE_URL:
    print("Error: No URL provided.")
    exit(1)

def reset_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Connected to PRODUCTION database...")
        
        print("Deleting Transactions...")
        cur.execute("DELETE FROM transactions;")
        
        print("Deleting Users...")
        cur.execute("DELETE FROM users;")
        
        print("Deleting Organizations...")
        cur.execute("DELETE FROM organizations;")
        
        conn.commit()
        print("✅ Production Database reset successfully! All users and organizations deleted.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()
