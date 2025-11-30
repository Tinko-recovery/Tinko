from sqlalchemy import create_engine, text

class DB:
    def __init__(self, dsn: str):
        self.engine = create_engine(dsn, future=True)

    def init(self):
        with open("db/schema.sql", "r", encoding="utf-8") as f:
            sql = f.read().lstrip("\ufeff")
        # Skip SQLite-specific PRAGMA when using Postgres/Neon
        if self.engine.dialect.name != "sqlite":
            sql = "\n".join(
                line for line in sql.splitlines() if not line.strip().upper().startswith("PRAGMA ")
            )
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        with self.engine.begin() as conn:
            for stmt in statements:
                conn.exec_driver_sql(stmt)

    def insert_event(self, **kwargs):
        sql = text("""
            INSERT INTO events
            (id, order_id, attempt_id, customer_id, event_type, status, failure_code, failure_message, amount, currency, raw_json)
            VALUES (:id, :order_id, :attempt_id, :customer_id, :event_type, :status, :failure_code, :failure_message, :amount, :currency, :raw_json)
        """)
        with self.engine.begin() as conn:
            conn.execute(sql, kwargs)

    def insert_attempt(self, **kwargs):
        sql = text("""
            INSERT INTO attempts
            (id, order_id, attempt_from_event, method, strategy, status)
            VALUES (:id, :order_id, :attempt_from_event, :method, :strategy, :status)
        """)
        with self.engine.begin() as conn:
            conn.execute(sql, kwargs)

    def list_events(self, limit: int = 50):
        sql = text("SELECT * FROM events ORDER BY created_at DESC LIMIT :limit")
        with self.engine.begin() as conn:
            rows = conn.execute(sql, {"limit": limit}).mappings().all()
        return [dict(r) for r in rows]

    def list_attempts(self, limit: int = 50):
        sql = text("SELECT * FROM attempts ORDER BY created_at DESC LIMIT :limit")
        with self.engine.begin() as conn:
            rows = conn.execute(sql, {"limit": limit}).mappings().all()
        return [dict(r) for r in rows]
