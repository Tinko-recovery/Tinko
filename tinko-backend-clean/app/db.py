import os
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    pass

# -----------------------
# DATABASE URL
# -----------------------
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please set a valid Postgres URL."
    )

parsed = urlparse(SQLALCHEMY_DATABASE_URL)
if not parsed.scheme.startswith("postgresql"):
    raise RuntimeError(
        f"Unsupported DATABASE_URL scheme '{parsed.scheme}'. Only Postgres is supported."
    )

# Ensure sslmode=require if missing
if "sslmode=" not in SQLALCHEMY_DATABASE_URL and parsed.scheme.startswith("postgresql"):
    sep = "&" if "?" in SQLALCHEMY_DATABASE_URL else "?"
    SQLALCHEMY_DATABASE_URL = f"{SQLALCHEMY_DATABASE_URL}{sep}sslmode=require"

# -----------------------
# SQLAlchemy Engine
# -----------------------
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# Base for ALL models
Base = declarative_base()

# -----------------------
# Dependency
# -----------------------
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
