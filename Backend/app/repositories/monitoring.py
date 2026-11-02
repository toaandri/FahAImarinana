from sqlalchemy import select, func
from ..models import SourceSurveillee, SignalBrut, DraftIA
from .base import Repository


class SourceRepository(Repository[SourceSurveillee]):
    model = SourceSurveillee


class SignalRepository(Repository[SignalBrut]):
    model = SignalBrut

    def count_between(self, start, end):
        return self.db.scalar(select(func.count(SignalBrut.id)).where(
            SignalBrut.horodatage_publication >= start,
            SignalBrut.horodatage_publication <= end)) or 0

    def pending_urgent(self):
        return list(self.db.scalars(select(SignalBrut).where(
            SignalBrut.est_urgent.is_(True),
            ~select(DraftIA.id).where(DraftIA.signal_id == SignalBrut.id).exists()
        ).order_by(SignalBrut.id)))
