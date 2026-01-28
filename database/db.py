from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# For development purposes, fallback to sqlite if no DATABASE_URL is provided or if it's the example one
if not DATABASE_URL or DATABASE_URL.startswith("postgresql://user:password"):
    DATABASE_URL = "sqlite:///./fitness_tracker.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import models here to ensure they are registered with Base.metadata before creation
    from database import models
    Base.metadata.create_all(bind=engine)