from sqlalchemy.orm import Session
from ..models import SourceSurveillee
from ..repositories import SourceRepository
from ..schemas import SourceCreate


def create_source(db: Session, payload: SourceCreate) -> SourceSurveillee:
    source = SourceSurveillee(**payload.model_dump(exclude={"url"}), url=str(payload.url))
    SourceRepository(db).add(source)
    db.commit()
    db.refresh(source)
    return source
