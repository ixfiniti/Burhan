from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from fastapi import Depends
from app.models.argument import Argument
from app.models.argument_evidence import ArgumentEvidence
from app.models.argument_premise import ArgumentPremise
from app.models.argument_response import ArgumentResponse

router = APIRouter(prefix="/evidence", tags=["Evidence"])

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def build_argument_link(evidence: ArgumentEvidence, db: Session) -> dict:
    parent_type = None
    parent_id = None
    parent_text = None
    argument = None

    if evidence.premise_id is not None:
        premise = db.get(ArgumentPremise, evidence.premise_id)

        if premise:
            parent_type = "premise"
            parent_id = premise.id
            parent_text = premise.statement
            argument = db.get(Argument, premise.argument_id)

    elif evidence.response_id is not None:
        response = db.get(ArgumentResponse, evidence.response_id)

        if response:
            parent_type = "response"
            parent_id = response.id
            parent_text = response.statement

            objection = response.objection

            if objection:
                argument = db.get(Argument, objection.argument_id)

    return {
        "evidence_id": evidence.id,
        "argument": (
            {
                "id": argument.id,
                "title": argument.title,
                "question": argument.question,
                "status": argument.status,
            }
            if argument
            else None
        ),
        "connection": {
            "type": parent_type,
            "id": parent_id,
            "text": parent_text,
        },
        "role": evidence.role,
        "reference": evidence.reference,
        "note": evidence.note,
    }
 
@router.get("/quran/{ayah_id}")
def get_quran_evidence(
    ayah_id: int,
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(ArgumentEvidence)
        .filter(
            ArgumentEvidence.result_type == "quran",
            ArgumentEvidence.result_id == ayah_id,
        )
        .all()
    )

    return {
        "result_type": "quran",
        "result_id": ayah_id,
        "total": len(evidence),
        "arguments": [
            build_argument_link(item, db)
            for item in evidence
        ],
    }


@router.get("/hadith/{hadith_id}")
def get_hadith_evidence(
    hadith_id: int,
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(ArgumentEvidence)
        .filter(
            ArgumentEvidence.result_type == "hadith",
            ArgumentEvidence.result_id == hadith_id,
        )
        .all()
    )

    return {
        "result_type": "hadith",
        "result_id": hadith_id,
        "total": len(evidence),
        "arguments": [
            build_argument_link(item, db)
            for item in evidence
        ],
    }