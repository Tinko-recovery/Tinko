import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    try:
        result = conn.execute(text("SELECT website, payment_gateways FROM organizations LIMIT 1;"))
        print("✅ Columns exist!")
    except Exception as e:
        print(f"❌ Columns missing: {e}")
