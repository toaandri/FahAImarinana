from sqlalchemy import Integer, String, Text, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from ..database.base import Base
from .common import ScopedRecord,scope_args,scoped_fk


class Contribution(ScopedRecord,Base):
    __tablename__='contributions'
    __table_args__=(*scope_args('contributions'),
        scoped_fk('submitted_by_id','users',name='fk_contribution_actor'),
        scoped_fk('parent_id','contributions',name='fk_contribution_parent'),
        CheckConstraint("kind IN ('signal','information')",name='ck_contribution_kind'),
        CheckConstraint("status IN ('submitted','reviewed','rejected')",name='ck_contribution_status'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    submitted_by_id: Mapped[int]=mapped_column(Integer,index=True)
    parent_id: Mapped[int|None]=mapped_column(Integer)
    kind: Mapped[str]=mapped_column(String(20))
    content: Mapped[str]=mapped_column(Text)
    reference_url: Mapped[str|None]=mapped_column(String(500))
    status: Mapped[str]=mapped_column(String(20),default='submitted')


class TechnicalSetting(ScopedRecord,Base):
    __tablename__='technical_settings'
    __table_args__=(*scope_args('technical_settings'),
        UniqueConstraint('newsroom_id','dataset','key',name='uq_setting_key_scope'),
        scoped_fk('updated_by_id','users',name='fk_setting_actor'),
        CheckConstraint("key IN ('ingestion_batch_size','research_result_limit')",name='ck_setting_key'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    key: Mapped[str]=mapped_column(String(80))
    value: Mapped[int]=mapped_column(Integer)
    updated_by_id: Mapped[int]=mapped_column(Integer)
