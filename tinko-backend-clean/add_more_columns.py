import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)

def add_column(column_sql):
    try:
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE organizations ADD COLUMN IF NOT EXISTS {column_sql};"))
            conn.commit()
            print(f"✅ Added column: {column_sql}")
    except Exception as e:
        print(f"⚠️ Could not add column {column_sql}: {e}")

print("🚀 Starting Phase 2 schema migration...")

add_column("business_size VARCHAR(32)")
add_column("monthly_gmv VARCHAR(32)")
add_column("recovery_destination VARCHAR(32) DEFAULT 'customer'")
add_column("gateway_credentials JSONB DEFAULT '{}'::jsonb")
add_column("brand_name VARCHAR(128)")
add_column("support_email VARCHAR(255)")
add_column("reply_to_email VARCHAR(255)")
add_column("logo_url VARCHAR(512)")
add_column("team_contacts JSONB DEFAULT '{}'::jsonb")
add_column("billing_email VARCHAR(255)")

print("🏁 Migration complete.")
