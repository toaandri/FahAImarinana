import os
from collections.abc import Generator
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL or DATABASE_URL.startswith("******"):
    database_user = quote_plus(os.getenv("DATABASE_USER", "fanilo"))
    database_password = quote_plus(os.getenv("DATABASE_PASSWORD", "fanilo"))
    database_host = os.getenv("DATABASE_HOST", "localhost")
    database_port = os.getenv("DATABASE_PORT", "5432")
    database_name = os.getenv("DATABASE_NAME", "fanilo")
    DATABASE_URL = (
        f"postgresql+psycopg://{database_user}:{database_password}"
        f"@{database_host}:{database_port}/{database_name}"
    )

engine_options = {"pool_pre_ping": True}
if not DATABASE_URL.startswith("sqlite"):
    engine_options.update(
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    )
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
