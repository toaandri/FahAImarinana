"""Explicit administrative sessions for test setup; never used by HTTP dependencies."""
from ..database import Base, SessionLocal, engine
from ..database.public import create_public_views, drop_public_views
from ..database.guards import install_guards
from ..models import Newsroom


def system_session():
    return SessionLocal(info={'system': True})


def reset_schema():
    with engine.begin() as connection:
        drop_public_views(connection)
        Base.metadata.drop_all(connection)
        Base.metadata.create_all(connection)
        create_public_views(connection)
        install_guards(connection, Base.metadata.tables)
        connection.execute(Newsroom.__table__.insert(), [
            {'id': 1, 'slug': 'test-real', 'name': 'Test real newsroom', 'dataset': 'real', 'status': 'active'},
            {'id': 2, 'slug': 'test-quarantine', 'name': 'Unclassified archives', 'dataset': 'quarantine', 'status': 'active'},
        ])
        if connection.dialect.name == 'postgresql':
            from sqlalchemy import text
            connection.execute(text("SELECT setval(pg_get_serial_sequence('newsrooms','id'),2,true)"))
