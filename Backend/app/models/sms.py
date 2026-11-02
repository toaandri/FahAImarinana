from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from ..database.base import Base


class HistoriqueSms(Base):
    __tablename__ = "historique_sms"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_expediteur: Mapped[str] = mapped_column(String(30))
    message_recu: Mapped[str] = mapped_column(Text)
    message_envoye: Mapped[str] = mapped_column(Text)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    statut_reponse: Mapped[str] = mapped_column(String(30))
