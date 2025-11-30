from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import text

from app.db import engine


def _month_bounds(dt: datetime):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


essential_notice = "Partition attach skipped (parent may not be partitioned)."


def ensure_current_month_partitions() -> List[str]:
    """Ensure current and next month partitions exist for transactions.

    - Postgres: create child tables and attempt ATTACH PARTITION (if parent is partitioned).
    - Other dialects (e.g., SQLite): no-op.

    Returns a list of partition table names touched/ensured.
    """
    created: List[str] = []
    dialect = engine.dialect.name
    if dialect != "postgresql":
        return created

    now = datetime.now(timezone.utc)
    months = [now, (now.replace(day=28) + timedelta(days=4))]

    with engine.begin() as conn:
        for m in months:
            start, end = _month_bounds(m)
            suffix = f"y{start.year}m{start.month:02d}"
            part_table = f"transactions_{suffix}"
            sql = f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = '{part_table}' AND n.nspname = 'public'
                ) THEN
                    EXECUTE 'CREATE TABLE public.{part_table} (LIKE public.transactions INCLUDING ALL)';
                END IF;
                BEGIN
                    EXECUTE 'ALTER TABLE public.transactions ATTACH PARTITION public.{part_table} FOR VALUES FROM (\"{start.isoformat()}\") TO (\"{end.isoformat()}\")';
                EXCEPTION WHEN others THEN
                    RAISE NOTICE '{essential_notice}';
                END;
            END $$;
            """
            conn.execute(text(sql))
            created.append(part_table)

    return created


def prune_old_partitions(months: int) -> List[str]:
    """Drop monthly partitions older than N months.

    - Postgres: DROP TABLE public.transactions_yYYYmMM
    - Others (e.g., SQLite): return []
    """
    dropped: List[str] = []
    if engine.dialect.name != "postgresql":
        return dropped

    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

    with engine.begin() as conn:
        # Find existing partition tables matching naming pattern
        res = conn.execute(text("""
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname LIKE 'transactions_y%m%'
        """))
        for (relname,) in res.fetchall():
            try:
                # Parse suffix to date
                # relname e.g., transactions_y2025m01
                parts = relname.split('_')
                suffix = parts[-1]
                year = int(suffix[1:5])
                month = int(suffix[6:8])
                dt = datetime(year, month, 1, tzinfo=timezone.utc)
                if dt < cutoff:
                    conn.execute(text(f"DROP TABLE IF EXISTS public.{relname} CASCADE"))
                    dropped.append(relname)
            except Exception:
                # Ignore parsing errors
                pass

    return dropped
