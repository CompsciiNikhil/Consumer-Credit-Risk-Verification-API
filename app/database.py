"""
database.py — SQLAlchemy engine and session setup.
DATABASE_URL is read from environment / .env file.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./credit_risk.db")

# For SQLite in tests, we need check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency: yields a DB session and ensures it's closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
