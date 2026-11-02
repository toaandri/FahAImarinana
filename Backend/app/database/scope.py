"""Fail-closed ORM isolation. System sessions are for migrations/fixtures/operators only."""
from dataclasses import dataclass
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, with_loader_criteria
from ..core.errors import ForbiddenError, ConflictError
from ..models.common import ScopedRecord


@dataclass(frozen=True)
class DataScope:
    newsroom_id: int
    dataset: str


def set_scope(db: Session, newsroom_id: int, dataset: str) -> DataScope:
    if newsroom_id < 1 or dataset not in {'real', 'demo', 'quarantine'}:
        raise ForbiddenError('Périmètre de données invalide.')
    scope = DataScope(newsroom_id, dataset)
    previous = db.info.get('scope')
    if previous is not None and previous != scope:
        raise ForbiddenError('Une session ne peut pas changer de rédaction ou de jeu de données.')
    db.info['scope'] = scope
    return scope


def scope_for_user(db: Session, user) -> DataScope:
    return set_scope(db, user.newsroom_id, user.dataset)


def require_scope(db: Session) -> DataScope:
    scope = db.info.get('scope')
    if scope is None:
        raise ForbiddenError('Un périmètre de rédaction est requis.')
    return scope


@event.listens_for(Session, 'do_orm_execute')
def isolate_queries(state):
    if not state.is_orm_statement or state.session.info.get('system'):
        return
    if state.execution_options.get('authentication_lookup'):
        # This flag is an internal capability, never derived from request parameters.
        from ..models import User
        descriptions = getattr(state.statement, 'column_descriptions', [])
        if not descriptions or any(item.get('entity') is not User for item in descriptions):
            raise ForbiddenError('Recherche d’identité invalide.')
        return
    scope = require_scope(state.session)
    newsroom_id, dataset = scope.newsroom_id, scope.dataset
    state.statement = state.statement.options(with_loader_criteria(
        ScopedRecord,
        lambda entity: (entity.newsroom_id == newsroom_id) & (entity.dataset == dataset),
        include_aliases=True,
    ))


@event.listens_for(Session, 'before_flush')
def isolate_writes(db, flush_context, instances):
    from ..models import CorrectionAudit
    for entity in set(db.new) | set(db.dirty) | set(db.deleted):
        if isinstance(entity, CorrectionAudit) and entity not in db.new:
            if entity in db.deleted or db.is_modified(entity):
                raise ConflictError('Le journal des corrections est immuable.')
        if not isinstance(entity, ScopedRecord) or db.info.get('system'):
            continue
        scope = require_scope(db)
        if entity in db.new:
            if entity.newsroom_id is None:
                entity.newsroom_id = scope.newsroom_id
            if entity.dataset is None:
                entity.dataset = scope.dataset
        if (entity.newsroom_id, entity.dataset) != (scope.newsroom_id, scope.dataset):
            raise ForbiddenError('Écriture hors du périmètre de rédaction.')
        state = inspect(entity)
        if state.persistent and any(state.attrs[name].history.has_changes() for name in ('newsroom_id', 'dataset')):
            raise ForbiddenError('Le périmètre d’un enregistrement est immuable.')
