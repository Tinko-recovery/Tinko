import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM users;")
    count = cur.fetchone()[0]
    print(f"User count: {count}")
    cur.close()
    conn.close()
except Exception as e:
    print(e)
