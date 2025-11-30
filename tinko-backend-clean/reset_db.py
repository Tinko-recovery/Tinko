import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

def reset_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Connected to database...")
        
        # Delete in order to respect foreign key constraints
        # 1. Transactions (depend on users/orgs)
        # 2. Users (depend on orgs sometimes, or orgs depend on users - check circular)
        # Actually, User has org_id (FK to Organization). Organization doesn't usually have FK to User.
        # So we should delete Users first? No, if User has FK to Org, we can delete User, then Org.
        
        print("Deleting Transactions...")
        cur.execute("DELETE FROM transactions;")
        
        print("Deleting Users...")
        cur.execute("DELETE FROM users;")
        
        print("Deleting Organizations...")
        cur.execute("DELETE FROM organizations;")
        
        conn.commit()
        print("✅ Database reset successfully! All users and organizations deleted.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()
