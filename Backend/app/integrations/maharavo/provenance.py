"""Trusted backend snapshots, never consultation claims supplied by a model.

Recording materialized text proves only the backend's read of that snapshot.
A future provider adapter must additionally document its actual consultation trace.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from types import MappingProxyType
from uuid import UUID, uuid4
from .contracts import DocumentInput


@dataclass(frozen=True)
class ConsultationManifest:
    task_id: UUID
    newsroom_id: int
    dataset: str
    documents: tuple[DocumentInput, ...]

    def __post_init__(self):
        if self.newsroom_id < 1 or self.dataset not in {'real', 'demo', 'quarantine'}:
            raise ValueError('Invalid backend scope')
        ids = [item.document_id for item in self.documents]
        receipts = [item.consultation_id for item in self.documents]
        if len(ids) != len(set(ids)) or len(receipts) != len(set(receipts)):
            raise ValueError('Duplicate backend consultation identity')
        if any(hashlib.sha256(item.text.encode()).hexdigest() != item.sha256 for item in self.documents):
            raise ValueError('Snapshot digest does not match materialized text')

    @property
    def by_id(self):
        return MappingProxyType({item.document_id: item for item in self.documents})


def record_materialized_document(*, document_id: UUID, url: str, text: str) -> DocumentInput:
    """Called by a trusted backend reader after materialization, not by an HTTP DTO."""
    return DocumentInput(document_id=document_id, consultation_id=uuid4(), url=url,
        sha256=hashlib.sha256(text.encode()).hexdigest(), text=text, consulted_at=datetime.now(timezone.utc))
