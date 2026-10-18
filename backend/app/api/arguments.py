from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.argument import Argument
from sqlalchemy import or_
from app.models.argument_category import ArgumentCategory
from app.models.argument_objection import ArgumentObjection
from app.models.argument_premise import ArgumentPremise
from app.services.evidence import resolve_evidence_result
from app.models.argument_response import ArgumentResponse
from app.schemas.argument import (
    ArgumentCategoryResponse,
    ArgumentCreate,
    ArgumentResponse as ArgumentResponseSchema,
)


router = APIRouter(
    prefix="/arguments",
    tags=["Arguments"],
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
# Validation helpers
# ---------------------------------------------------------


def validate_text(
    value: str,
    field_name: str,
) -> str:
    cleaned = value.strip()

    if not cleaned:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} cannot be empty",
        )

    return cleaned


def validate_unique_numbers(
    numbers: list[int],
    item_name: str,
) -> None:
    if len(numbers) != len(set(numbers)):
        raise HTTPException(
            status_code=422,
            detail=(
                f"{item_name} numbers must be unique"
            ),
        )


# ---------------------------------------------------------
# Categories
# ---------------------------------------------------------


@router.get(
    "/categories",
    response_model=list[ArgumentCategoryResponse],
)
def list_argument_categories(
    db: Session = Depends(get_db),
):
    return (
        db.query(ArgumentCategory)
        .order_by(ArgumentCategory.name)
        .all()
    )


# ---------------------------------------------------------
# List Arguments
# ---------------------------------------------------------


@router.get(
    "",
    response_model=list[ArgumentResponseSchema],
)
def list_arguments(
    db: Session = Depends(get_db),
):
    return (
        db.query(Argument)
        .order_by(Argument.id)
        .all()
    )


# ---------------------------------------------------------
# Create Argument
# ---------------------------------------------------------


@router.post(
    "",
    response_model=ArgumentResponseSchema,
)
def create_argument(
    data: ArgumentCreate,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Validate category
    # -----------------------------------------------------

    category = db.get(
        ArgumentCategory,
        data.category_id,
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Argument category not found",
        )

    # -----------------------------------------------------
    # Validate argument text
    # -----------------------------------------------------

    title = validate_text(
        data.title,
        "title",
    )

    question = validate_text(
        data.question,
        "question",
    )

    summary = (
        data.summary.strip()
        if data.summary is not None
        else None
    )

    claim = (
        data.claim.strip()
        if data.claim is not None
        else None
    )

    conclusion = (
        data.conclusion.strip()
        if data.conclusion is not None
        else None
    )

    # -----------------------------------------------------
    # Validate premise numbering
    # -----------------------------------------------------

    validate_unique_numbers(
        [premise.number for premise in data.premises],
        "Premise",
    )

    # -----------------------------------------------------
    # Validate objection numbering
    # -----------------------------------------------------

    validate_unique_numbers(
        [objection.number for objection in data.objections],
        "Objection",
    )

    # -----------------------------------------------------
    # Validate response numbering
    # -----------------------------------------------------

    for objection in data.objections:
        validate_unique_numbers(
            [
                response.number
                for response in objection.responses
            ],
            (
                f"Response numbers for objection "
                f"{objection.number}"
            ),
        )

    # -----------------------------------------------------
    # Create argument
    # -----------------------------------------------------

    argument = Argument(
        category_id=data.category_id,
        title=title,
        question=question,
        summary=summary,
        claim=claim,
        conclusion=conclusion,
        status=data.status,
    )

    db.add(argument)
    db.flush()

    # -----------------------------------------------------
    # Create premises
    # -----------------------------------------------------

    for premise_data in data.premises:
        premise = ArgumentPremise(
            argument_id=argument.id,
            number=premise_data.number,
            statement=validate_text(
                premise_data.statement,
                (
                    f"Premise "
                    f"{premise_data.number} statement"
                ),
            ),
            description=(
                premise_data.description.strip()
                if premise_data.description is not None
                else None
            ),
        )

        db.add(premise)

    # -----------------------------------------------------
    # Create objections and responses
    # -----------------------------------------------------

    for objection_data in data.objections:
        objection = ArgumentObjection(
            argument_id=argument.id,
            number=objection_data.number,
            statement=validate_text(
                objection_data.statement,
                (
                    f"Objection "
                    f"{objection_data.number} statement"
                ),
            ),
            description=(
                objection_data.description.strip()
                if objection_data.description is not None
                else None
            ),
        )

        db.add(objection)
        db.flush()

        for response_data in objection_data.responses:
            response = ArgumentResponse(
                objection_id=objection.id,
                number=response_data.number,
                statement=validate_text(
                    response_data.statement,
                    (
                        f"Response "
                        f"{response_data.number} statement"
                    ),
                ),
                description=(
                    response_data.description.strip()
                    if response_data.description is not None
                    else None
                ),
            )

            db.add(response)

    # -----------------------------------------------------
    # Commit atomically
    # -----------------------------------------------------

    db.commit()
    db.refresh(argument)

    return argument


# ---------------------------------------------------------
# Search Arguments
# ---------------------------------------------------------

@router.get("/search")
def search_arguments(
    q: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query_text = q.strip()

    if not query_text:
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="Limit must be between 1 and 100",
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="Offset cannot be negative",
        )

    pattern = f"%{query_text}%"

    matching_premise = Argument.premises.any(
        ArgumentPremise.statement.ilike(pattern)
    )

    matching_objection = Argument.objections.any(
        or_(
            ArgumentObjection.statement.ilike(pattern),
            ArgumentObjection.responses.any(
                ArgumentResponse.statement.ilike(pattern)
            ),
        )
    )

    filters = or_(
        Argument.title.ilike(pattern),
        Argument.question.ilike(pattern),
        Argument.summary.ilike(pattern),
        Argument.claim.ilike(pattern),
        Argument.conclusion.ilike(pattern),
        Argument.category.has(
            ArgumentCategory.name.ilike(pattern)
        ),
        matching_premise,
        matching_objection,
    )

    base_query = db.query(Argument).filter(filters)
    total = base_query.count()

    arguments = (
        base_query
        .order_by(Argument.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "results": [
            {
                "id": argument.id,
                "result_type": "argument",
                "reference": f"Argument #{argument.id}",
                "title": argument.title,
                "question": argument.question,
                "summary": argument.summary,
                "claim": argument.claim,
                "conclusion": argument.conclusion,
                "status": argument.status,
                "category": {
                    "id": argument.category.id,
                    "name": argument.category.name,
                    "slug": argument.category.slug,
                },
            }
            for argument in arguments
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(arguments) < total,
    }

# ---------------------------------------------------------
# Get Argument
# ---------------------------------------------------------


@router.get(
    "/{argument_id}",
    response_model=ArgumentResponseSchema,
)
def get_argument(
    argument_id: int,
    db: Session = Depends(get_db),
):
    argument = db.get(
        Argument,
        argument_id,
    )

    if argument is None:
        raise HTTPException(
            status_code=404,
            detail="Argument not found",
        )

    def build_evidence(evidence):
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

    return {
        "id": argument.id,
        "category_id": argument.category_id,

        "title": argument.title,
        "question": argument.question,
        "summary": argument.summary,
        "claim": argument.claim,
        "conclusion": argument.conclusion,
        "status": argument.status,

        "category": {
            "id": argument.category.id,
            "name": argument.category.name,
            "slug": argument.category.slug,
            "description": argument.category.description,
        },

        "premises": [
            {
                "id": premise.id,
                "number": premise.number,
                "statement": premise.statement,
                "description": premise.description,
                "evidence": [
                    build_evidence(evidence)
                    for evidence in premise.evidence
                ],
            }
            for premise in sorted(
                argument.premises,
                key=lambda item: item.number,
            )
        ],

        "objections": [
            {
                "id": objection.id,
                "number": objection.number,
                "statement": objection.statement,
                "description": objection.description,

                "responses": [
                    {
                        "id": response.id,
                        "number": response.number,
                        "statement": response.statement,
                        "description": response.description,
                        "evidence": [
                            build_evidence(evidence)
                            for evidence in response.evidence
                        ],
                    }
                    for response in sorted(
                        objection.responses,
                        key=lambda item: item.number,
                    )
                ],
            }
            for objection in sorted(
                argument.objections,
                key=lambda item: item.number,
            )
        ],
    }


# ---------------------------------------------------------
# Update Evidence
# ---------------------------------------------------------

EVIDENCE_ROLES = {
    "direct",
    "consequence",
    "conceptual",
    "contextual",
    "related",
    "incidental",
    "supporting",
}


class EvidenceUpdate(BaseModel):
    role: str
    note: str | None = None


@router.patch(
    "/{argument_id}/evidence/{evidence_id}",
)
def update_evidence(
    argument_id: int,
    evidence_id: int,
    data: EvidenceUpdate,
    db: Session = Depends(get_db),
):
    argument = db.get(
        Argument,
        argument_id,
    )

    if argument is None:
        raise HTTPException(
            status_code=404,
            detail="Argument not found",
        )

    role = data.role.strip().lower().replace(" ", "_")

    if role not in EVIDENCE_ROLES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Role must be one of: "
                + ", ".join(sorted(EVIDENCE_ROLES))
            ),
        )

    note = (
        data.note.strip() or None
        if data.note is not None
        else None
    )

    # Look for the evidence only inside this argument, so an
    # evidence ID from another argument cannot be edited here.
    target = None

    for premise in argument.premises:
        for evidence in premise.evidence:
            if evidence.id == evidence_id:
                target = evidence

    for objection in argument.objections:
        for response in objection.responses:
            for evidence in response.evidence:
                if evidence.id == evidence_id:
                    target = evidence

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found in this argument",
        )

    target.role = role
    target.note = note

    db.commit()
    db.refresh(target)

    return {
        "id": target.id,
        "role": target.role,
        "note": target.note,
    }


# ---------------------------------------------------------
# Delete Argument
# ---------------------------------------------------------


@router.delete(
    "/{argument_id}",
)
def delete_argument(
    argument_id: int,
    db: Session = Depends(get_db),
):
    argument = db.get(
        Argument,
        argument_id,
    )

    if argument is None:
        raise HTTPException(
            status_code=404,
            detail="Argument not found",
        )

    db.delete(argument)
    db.commit()

    return {
        "message": "Argument deleted",
        "id": argument_id,
    }