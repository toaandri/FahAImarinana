"""Database dependency and backwards compatible public exports."""
from .base import Base
from .connection import DATABASE_URL, SessionLocal, engine, get_db, get_public_db, public_engine
from . import scope  # install fail-closed query/write isolation
