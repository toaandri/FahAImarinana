from fastapi import APIRouter

router = APIRouter(tags=["Système"])


@router.get("/health")
def health():
    return {"status": "ok"}
