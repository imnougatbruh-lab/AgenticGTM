import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get the database URL from .env, default to SQLite for frictionless local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agenticgtm.db")

# Fix for Heroku/Render standard 'postgres://' scheme prefix deprecation issues
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fix for SQLite thread issues in FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    print(f"Attempting connection to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Test connection immediately to catch config/availability issues
    with engine.connect() as conn:
        print("Database connection test successful!")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Connection to database failed: {e}")
    print("Falling back to local SQLite database for frictionless offline development...")
    DATABASE_URL = "sqlite:///./agenticgtm.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency that yields a database session.
    Automatically closes the session when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes the database by creating all tables.
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")
