from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.ai_context import AIContextResponse
from app.services.ai_context import build_ai_context


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/context/{evidence_set_id}",
    response_model=AIContextResponse,
)
def get_ai_context(
    evidence_set_id: int,
    db: Session = Depends(get_db),
):
    try:
        return build_ai_context(
            evidence_set_id=evidence_set_id,
            db=db,
        )

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Evidence set not found",
        )