from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import SmsRequest, SmsResponse
from ..services import answer_citizen_sms

router = APIRouter(prefix="/sms", tags=["SMS"])


@router.post("/citizen", response_model=SmsResponse)
def citizen_sms(payload: SmsRequest, db: Session = Depends(get_db)):
    message, response_status = answer_citizen_sms(db, payload)
    return {"message": message, "statut": response_status}
