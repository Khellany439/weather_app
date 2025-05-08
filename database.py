import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Get database URL from environment variable or use SQLite as fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./weather_service.db")

# Create database engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_recycle=300
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI to get database session
def get_db_fastapi():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for Flask to get database session
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple function to get a database session without context management
def get_db_session():
    return SessionLocal()
