from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.evidence_set import EvidenceSet
from app.schemas.ai_answer import AIAnswerResponse
from app.schemas.ai_context import AIContextResponse
from app.services.ai_answer import build_ai_answer
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


@router.post(
    "/answer/{evidence_set_id}",
    response_model=AIAnswerResponse,
)
def get_ai_answer(
    evidence_set_id: int,
    db: Session = Depends(get_db),
):
    evidence_set = (
        db.query(EvidenceSet)
        .filter(EvidenceSet.id == evidence_set_id)
        .first()
    )

    if evidence_set is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence set not found",
        )

    context: AIContextResponse = build_ai_context(
        evidence_set_id=evidence_set_id,
        db=db,
    )

    try:
        return build_ai_answer(context)

    except ValueError as exc:
        error_data = exc.args[0]

        if isinstance(error_data, dict):
            return JSONResponse(
                status_code=422,
                content={
                    "status": "rejected",
                    "reason": error_data.get(
                        "message",
                        "The generated answer could not be fully grounded.",
                    ),
                    "issues": error_data.get("issues", []),
                },
            )

        raise