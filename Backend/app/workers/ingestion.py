"""Supervised synchronous batch; external scheduler may call run()."""
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..database.scope import set_scope
from ..core.config import get_settings
from ..repositories import SignalRepository
from ..services.signals import cross_check_signal
from ..services.drafts import create_draft


def process_pending_signals(db: Session) -> int:
    processed = 0
    for signal in SignalRepository(db).pending_urgent():
        create_draft(db, signal, cross_check_signal(db, signal))
        processed += 1
    return processed


def run() -> int:
    with SessionLocal() as db:
        settings = get_settings()
        set_scope(db, settings.default_newsroom_id, settings.default_dataset)
        try:
            return process_pending_signals(db)
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    print({"processed": run()})
