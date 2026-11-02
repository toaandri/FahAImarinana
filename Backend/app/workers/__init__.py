"""Callable jobs; no background scheduler is started implicitly."""


def process_pending_signals(db):
    """Compatibility entry point without eager import of executable job modules."""
    from .ingestion import process_pending_signals as process
    return process(db)
