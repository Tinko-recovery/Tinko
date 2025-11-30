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

print("🚀 Starting schema migration...")

add_column("website VARCHAR(255)")
add_column("industry VARCHAR(64)")
add_column("gst_number VARCHAR(32)")
add_column("payment_gateways JSONB DEFAULT '[]'::jsonb")
add_column("monthly_volume VARCHAR(32)")
add_column("recovery_channels JSONB DEFAULT '[]'::jsonb")

print("🏁 Migration complete.")
