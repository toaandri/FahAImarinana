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


_TEST_HASH=None


def make_account(role='JOURNALISTE',email=None,newsroom_id=1,dataset='real',service_permissions=None):
    global _TEST_HASH
    from ..models import User
    from ..core.security import password_hash
    from ..core.rbac import Role,ROLE_PERMISSIONS
    if _TEST_HASH is None:
        _TEST_HASH=password_hash('password123')
    role=Role(role)
    with system_session() as db:
        user=User(email=email or role.value.lower()+'@example.invalid',role=role.value,
            account_type='service' if role==Role.SERVICE_IA else 'human',
            service_permissions=list(service_permissions if service_permissions is not None else ROLE_PERMISSIONS[role]) if role==Role.SERVICE_IA else [],
            mot_de_passe_hash=_TEST_HASH,newsroom_id=newsroom_id,dataset=dataset)
        db.add(user); db.commit()
        return user


def tokens_for(user):
    from ..services.auth import issue_tokens
    with SessionLocal() as db:
        from ..repositories.identity import UserRepository
        current=UserRepository(db).get_for_auth(user.id)
        return issue_tokens(db,current)
