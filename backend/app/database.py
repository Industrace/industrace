# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://cmdb_user:secure_password_123@localhost:5432/cmdb_ics"
)

_connect_args: dict = {}
if DATABASE_URL.startswith("postgresql"):
    _connect_args = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000",
    }

# Configure engine with connection pool settings for better reliability
# Increased pool size to handle initialization and concurrent requests
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Increased from 5 to handle initialization
    max_overflow=20,  # Increased from 10 to handle peak loads
    pool_pre_ping=True,  # Verify connections before using them (prevents stale connections)
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=60,  # Increased timeout to 60 seconds
    echo=False,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
