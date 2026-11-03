"""Only hashes of refresh/invitation secrets are persisted."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk


def identifier():
    return uuid4().hex


class AuthSession(ScopedRecord,Base):
    __tablename__='auth_sessions'
    __table_args__=(*scope_args('auth_sessions'),
        scoped_fk('user_id','users',name='fk_auth_sessions_user'),
        CheckConstraint('auth_version >= 1',name='ck_auth_sessions_version'),
        CheckConstraint('expires_at > created_at',name='ck_auth_sessions_expiry'),
        Index('ix_auth_sessions_user_revoked','user_id','revoked_at'),
    )
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=identifier)
    user_id: Mapped[int]=mapped_column(Integer)
    auth_version: Mapped[int]=mapped_column(Integer)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str|None]=mapped_column(String(100))
    user_agent: Mapped[str]=mapped_column(String(250),default='')
    user: Mapped['User']=relationship(primaryjoin='AuthSession.user_id == User.id',foreign_keys=[user_id])


class RefreshToken(ScopedRecord,Base):
    __tablename__='refresh_tokens'
    __table_args__=(*scope_args('refresh_tokens'),
        scoped_fk('session_id','auth_sessions',name='fk_refresh_session'),
        Index('ix_refresh_session','session_id'),
        Index('ix_refresh_expiry','expires_at'),
    )
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=identifier)
    session_id: Mapped[str]=mapped_column(String(32))
    token_hash: Mapped[str]=mapped_column(String(64),unique=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    session: Mapped['AuthSession']=relationship(primaryjoin='RefreshToken.session_id == AuthSession.id',foreign_keys=[session_id])


class Invitation(ScopedRecord,Base):
    __tablename__='invitations'
    __table_args__=(*scope_args('invitations'),
        scoped_fk('invited_by_id','users',name='fk_invitation_actor'),
        CheckConstraint("role = 'JOURNALISTE'",name='ck_invitation_role'),
        Index('ix_invitation_email','email'),
    )
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=identifier)
    email: Mapped[str]=mapped_column(String(255))
    role: Mapped[str]=mapped_column(String(30))
    invited_by_id: Mapped[int]=mapped_column(Integer)
    token_hash: Mapped[str]=mapped_column(String(64),unique=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
