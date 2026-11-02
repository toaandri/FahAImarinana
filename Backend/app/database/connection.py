from collections.abc import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from ..core.config import get_settings

settings = get_settings()
DATABASE_URL = settings.sqlalchemy_url
options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    options["connect_args"] = {"check_same_thread": False}
    if ":memory:" in DATABASE_URL:
        options["poolclass"] = StaticPool
else:
    options.update(pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow)
engine = create_engine(DATABASE_URL, **options)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def sqlite_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise
