from typing import Generic, TypeVar
from sqlalchemy.orm import Session
from ..database.base import Base

Model = TypeVar("Model", bound=Base)


class Repository(Generic[Model]):
    """Persistence operations; transaction boundaries belong to services."""
    model: type[Model]

    def __init__(self, db: Session):
        self.db = db

    def get(self, identifier: int) -> Model | None:
        return self.db.get(self.model, identifier)

    def add(self, entity: Model) -> Model:
        self.db.add(entity)
        return entity
