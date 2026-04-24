

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# The engine is the actual connection to PostgreSQL.
# It manages the connection pool (multiple connections for concurrent requests).
engine = create_engine(settings.DATABASE_URL)

# SessionLocal is a factory that creates new DB sessions.
# Each request gets its own session — this is critical for safety.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all your models will inherit from.
# SQLAlchemy uses it to track which Python classes map to which tables.
Base = declarative_base()


# This is a FastAPI "dependency" — a function that provides a DB session
# to any route that needs it, and closes it automatically when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
