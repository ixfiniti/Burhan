from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.evidence_item import EvidenceItem
from app.models.evidence_set import EvidenceSet
from app.models.source import Source
from app.schemas.evidence_set import (
    EvidenceItemResponse,
    EvidenceSetCreate,
    EvidenceSetResponse,
    EvidenceSourceResponse,
)
from app.services.evidence import resolve_evidence_result


router = APIRouter(
    prefix="/evidence-sets",
    tags=["Evidence Sets"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def build_source_response(
    source: Source,
) -> EvidenceSourceResponse:
    return EvidenceSourceResponse(
        id=source.id,
        name=source.name,
        slug=source.slug,
        source_type=source.source_type,
        language=source.language,
        author=source.author,
        publisher=source.publisher,
        url=source.url,
        license=source.license,
        version=source.version,
        provenance_note=source.provenance_note,
        description=source.description,
    )


def build_evidence_item_response(
    item: EvidenceItem,
    db: Session,
) -> EvidenceItemResponse:
    resolved = resolve_evidence_result(
        result_type=item.result_type,
        result_id=item.result_id,
        source_id=item.source_id,
        db=db,
    )

    return EvidenceItemResponse(
        id=item.id,
        result_type=item.result_type,
        result_id=item.result_id,
        reference=item.reference,
        source_id=item.source_id,
        score=item.score,
        title=resolved["title"],
        collection=resolved["collection"],
        book_number=resolved["book_number"],
        book_name=resolved["book_name"],
        narrator=resolved["narrator"],
        text_arabic=resolved["text_arabic"],
        translation=resolved["translation"],
        translator=resolved["translator"],
        source=resolved["source"],
        primary_source=resolved["primary_source"],
        translation_source=resolved["translation_source"],
    )


@router.post(
    "",
    response_model=EvidenceSetResponse,
)
def create_evidence_set(
    data: EvidenceSetCreate,
    db: Session = Depends(get_db),
):
    evidence_set = EvidenceSet(
        query=data.query,
    )

    db.add(evidence_set)
    db.flush()

    for item in data.items:
        evidence_item = EvidenceItem(
            evidence_set_id=evidence_set.id,
            result_type=item.result_type,
            result_id=item.result_id,
            reference=item.reference,
            source_id=item.source_id,
            score=item.score,
        )

        db.add(evidence_item)

    db.commit()
    db.refresh(evidence_set)

    items = [
        build_evidence_item_response(item, db)
        for item in evidence_set.items
    ]

    return EvidenceSetResponse(
        id=evidence_set.id,
        query=evidence_set.query,
        created_at=evidence_set.created_at,
        items=items,
    )


@router.get(
    "/{evidence_set_id}",
    response_model=EvidenceSetResponse,
)
def get_evidence_set(
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

    items = [
        build_evidence_item_response(item, db)
        for item in evidence_set.items
    ]

    return EvidenceSetResponse(
        id=evidence_set.id,
        query=evidence_set.query,
        created_at=evidence_set.created_at,
        items=items,
    )