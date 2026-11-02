from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DraftIA, SignalBrut
from ..services import create_draft, cross_check_signal


def process_pending_signals(db: Session) -> int:
    """Process urgent signals; call this from cron, Celery, or a scheduler."""
    signals = db.scalars(
        select(SignalBrut).where(SignalBrut.est_urgent.is_(True))
    ).all()
    processed = 0
    for signal in signals:
        already_processed = db.scalar(
            select(DraftIA.id).where(DraftIA.signal_id == signal.id).limit(1)
        )
        if already_processed is None:
            sources = cross_check_signal(db, signal)
            create_draft(db, signal, sources)
            processed += 1
    return processed
