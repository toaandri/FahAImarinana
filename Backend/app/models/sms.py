from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk

class SmsExchange(ScopedRecord, Base):
    __tablename__ = 'sms_exchanges'
    __table_args__ = (*scope_args('sms_exchanges', public=False),
        scoped_fk("publication_id", "publications", name="fk_sms_publication_scope"),
        CheckConstraint("delivery_status IN ('received','simulated','queued','sent','delivered','failed')", name="ck_sms_delivery"),
        CheckConstraint("statut_reponse IN ('Trouve','Non_Trouve','Pending','Failed')", name="ck_sms_response"),
        Index("ix_sms_publication", "publication_id"),
        Index("ix_sms_phone_date", "numero_expediteur", "horodatage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_expediteur: Mapped[str] = mapped_column(String(30))
    message_recu: Mapped[str] = mapped_column(Text)
    message_envoye: Mapped[str] = mapped_column(Text)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    statut_reponse: Mapped[str] = mapped_column(String(30))

    publication_id: Mapped[int | None] = mapped_column(Integer)
    delivery_status: Mapped[str] = mapped_column(String(20), default="simulated")
    provider_message_id: Mapped[str | None] = mapped_column(String(150), unique=True)
    status = synonym("statut_reponse")
    publication: Mapped["Publication | None"] = relationship(primaryjoin="SmsExchange.publication_id == Publication.id", foreign_keys=[publication_id], back_populates="sms_exchanges")
