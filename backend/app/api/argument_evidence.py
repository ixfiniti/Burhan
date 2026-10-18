from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.argument import Argument
from app.models.argument_evidence import ArgumentEvidence
from app.models.argument_premise import ArgumentPremise
from app.models.argument_response import ArgumentResponse
from app.models.ayah import Ayah
from app.models.hadith import Hadith
from app.models.source import Source
from app.schemas.argument import (
    ArgumentEvidenceCreate,
    ArgumentEvidenceResponse,
    ArgumentEvidenceUpdate,
)
from app.services.evidence import resolve_evidence_result

router = APIRouter(
    prefix="/arguments",
    tags=["Argument Evidence"],
)


# ---------------------------------------------------------
# Database dependency
# ---------------------------------------------------------


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Evidence validation
# ---------------------------------------------------------


def validate_evidence_target(
    data: ArgumentEvidenceCreate,
    db: Session,
) -> None:
    if data.result_type == "quran":
        ayah = (
            db.query(Ayah)
            .filter(Ayah.id == data.result_id)
            .first()
        )

        if ayah is None:
            raise HTTPException(
                status_code=404,
                detail=f"Qur'an ayah {data.result_id} not found",
            )

    elif data.result_type == "hadith":
        hadith = (
            db.query(Hadith)
            .filter(Hadith.id == data.result_id)
            .first()
        )

        if hadith is None:
            raise HTTPException(
                status_code=404,
                detail=f"Hadith {data.result_id} not found",
            )

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported evidence result type: "
                f"{data.result_type}"
            ),
        )


def validate_source(
    source_id: int | None,
    db: Session,
) -> None:
    if source_id is None:
        return

    source = (
        db.query(Source)
        .filter(Source.id == source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail=f"Source {source_id} not found",
        )


# ---------------------------------------------------------
# Create evidence for a premise
# ---------------------------------------------------------


@router.post(
    "/{argument_id}/premises/{premise_id}/evidence",
    response_model=ArgumentEvidenceResponse,
)
def add_premise_evidence(
    argument_id: int,
    premise_id: int,
    data: ArgumentEvidenceCreate,
    db: Session = Depends(get_db),
):
    argument = (
        db.query(Argument)
        .filter(Argument.id == argument_id)
        .first()
    )

    if argument is None:
        raise HTTPException(
            status_code=404,
            detail="Argument not found",
        )

    premise = (
        db.query(ArgumentPremise)
        .filter(ArgumentPremise.id == premise_id)
        .first()
    )

    if premise is None:
        raise HTTPException(
            status_code=404,
            detail="Argument premise not found",
        )

    if premise.argument_id != argument.id:
        raise HTTPException(
            status_code=400,
            detail="Premise does not belong to this argument",
        )

    validate_evidence_target(
        data,
        db,
    )

    validate_source(
        data.source_id,
        db,
    )

    evidence = ArgumentEvidence(
        premise_id=premise.id,
        result_type=data.result_type,
        result_id=data.result_id,
        reference=(
            data.reference.strip()
            if data.reference is not None
            else None
        ),
        source_id=data.source_id,
        role=data.role.strip(),
        note=(
            data.note.strip()
            if data.note is not None
            else None
        ),
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


# ---------------------------------------------------------
# Create evidence for a response
# ---------------------------------------------------------


@router.post(
    "/{argument_id}/responses/{response_id}/evidence",
    response_model=ArgumentEvidenceResponse,
)
def add_response_evidence(
    argument_id: int,
    response_id: int,
    data: ArgumentEvidenceCreate,
    db: Session = Depends(get_db),
):
    argument = (
        db.query(Argument)
        .filter(Argument.id == argument_id)
        .first()
    )

    if argument is None:
        raise HTTPException(
            status_code=404,
            detail="Argument not found",
        )

    response = (
        db.query(ArgumentResponse)
        .filter(ArgumentResponse.id == response_id)
        .first()
    )

    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Argument response not found",
        )

    objection = response.objection

    if objection.argument_id != argument.id:
        raise HTTPException(
            status_code=400,
            detail="Response does not belong to this argument",
        )

    validate_evidence_target(
        data,
        db,
    )

    validate_source(
        data.source_id,
        db,
    )

    evidence = ArgumentEvidence(
        response_id=response.id,
        result_type=data.result_type,
        result_id=data.result_id,
        reference=(
            data.reference.strip()
            if data.reference is not None
            else None
        ),
        source_id=data.source_id,
        role=data.role.strip(),
        note=(
            data.note.strip()
            if data.note is not None
            else None
        ),
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


# ---------------------------------------------------------
# Delete argument evidence
# ---------------------------------------------------------


@router.delete(
    "/{argument_id}/evidence/{evidence_id}",
)
def delete_argument_evidence(
    argument_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(ArgumentEvidence)
        .filter(ArgumentEvidence.id == evidence_id)
        .first()
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Argument evidence not found",
        )

    belongs_to_argument = False

    if evidence.premise is not None:
        belongs_to_argument = (
            evidence.premise.argument_id == argument_id
        )

    elif evidence.response is not None:
        belongs_to_argument = (
            evidence.response.objection.argument_id
            == argument_id
        )

    if not belongs_to_argument:
        raise HTTPException(
            status_code=400,
            detail="Evidence does not belong to this argument",
        )

    db.delete(evidence)
    db.commit()

    return {
        "message": "Argument evidence deleted",
        "id": evidence_id,
    }

@router.get(
    "/{argument_id}/evidence/{evidence_id}",
)
def get_argument_evidence(
    argument_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(ArgumentEvidence)
        .filter(ArgumentEvidence.id == evidence_id)
        .first()
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Argument evidence not found",
        )

    belongs_to_argument = False

    if evidence.premise is not None:
        belongs_to_argument = (
            evidence.premise.argument_id == argument_id
        )

    elif evidence.response is not None:
        belongs_to_argument = (
            evidence.response.objection.argument_id
            == argument_id
        )

    if not belongs_to_argument:
        raise HTTPException(
            status_code=400,
            detail="Evidence does not belong to this argument",
        )

    resolved = resolve_evidence_result(
        result_type=evidence.result_type,
        result_id=evidence.result_id,
        source_id=evidence.source_id,
        db=db,
    )

    return {
        "id": evidence.id,
        "result_type": evidence.result_type,
        "result_id": evidence.result_id,
        "reference": evidence.reference,
        "source_id": evidence.source_id,
        "role": evidence.role,
        "note": evidence.note,
        "resolved": resolved,
    }


# ---------------------------------------------------------
# Update argument evidence
# ---------------------------------------------------------


@router.patch(
    "/{argument_id}/evidence/{evidence_id}",
    response_model=ArgumentEvidenceResponse,
)
def update_argument_evidence(
    argument_id: int,
    evidence_id: int,
    data: ArgumentEvidenceUpdate,
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(ArgumentEvidence)
        .filter(ArgumentEvidence.id == evidence_id)
        .first()
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Argument evidence not found",
        )

    belongs_to_argument = False

    if evidence.premise is not None:
        belongs_to_argument = (
            evidence.premise.argument_id == argument_id
        )

    elif evidence.response is not None:
        belongs_to_argument = (
            evidence.response.objection.argument_id
            == argument_id
        )

    if not belongs_to_argument:
        raise HTTPException(
            status_code=400,
            detail="Evidence does not belong to this argument",
        )

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No update fields provided",
        )

    if "role" in updates:
        role = updates["role"]

        if role is None:
            raise HTTPException(
                status_code=422,
                detail="Role cannot be null",
            )

        allowed_roles = {
            "direct",
            "consequence",
            "conceptual",
            "contextual",
            "related",
            "incidental",
            "supporting",
        }

        role = role.strip()

        if role not in allowed_roles:
            raise HTTPException(
                status_code=422,
                detail="Unsupported evidence role",
            )

        evidence.role = role

    if "note" in updates:
        note = updates["note"]

        evidence.note = (
            note.strip()
            if note is not None
            else None
        )

    db.commit()
    db.refresh(evidence)

    return evidence