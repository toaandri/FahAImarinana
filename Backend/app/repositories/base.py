from typing import Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..core.errors import NotFoundError, ForbiddenError
from ..database.base import Base

Model = TypeVar("Model", bound=Base)


class Repository(Generic[Model]):
    """Persistence operations; transaction boundaries belong to services."""
    model: type[Model]

    def __init__(self, db: Session):
        self.db = db

    def get(self, identifier: int) -> Model | None:
        return self.db.scalar(select(self.model).where(self.model.id == identifier))

    def add(self, entity: Model) -> Model:
        self.db.add(entity)
        return entity


    def list(self, *, limit: int = 100, offset: int = 0):
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("Pagination invalide.")
        return list(self.db.scalars(select(self.model).order_by(self.model.id).limit(limit).offset(offset)))

    def update(self, identifier: int, **changes):
        protected = {"id", "newsroom_id", "dataset", "created_at", "updated_at"}
        if protected & changes.keys():
            raise ForbiddenError("Ces champs sont gérés par le serveur.")
        entity = self.get(identifier)
        if entity is None:
            raise NotFoundError("Enregistrement introuvable.")
        from sqlalchemy import inspect
        columns = set(inspect(self.model).column_attrs.keys())
        if not changes.keys() <= columns:
            raise ValueError("Champ de mise à jour inconnu.")
        for name, value in changes.items():
            setattr(entity, name, value)
        self.db.flush()
        return entity

    def delete(self, identifier: int):
        entity = self.get(identifier)
        if entity is None:
            raise NotFoundError("Enregistrement introuvable.")
        self.db.delete(entity)
        self.db.flush()
