from sqlalchemy.orm import Session

from app.api.evidence_sets import build_evidence_item_response
from app.models.evidence_set import EvidenceSet
from app.schemas.ai_context import (
    AIContextEvidence,
    AIContextResponse,
)


def build_ai_context(
    evidence_set_id: int,
    db: Session,
) -> AIContextResponse:
    evidence_set = (
        db.query(EvidenceSet)
        .filter(EvidenceSet.id == evidence_set_id)
        .first()
    )

    if evidence_set is None:
        raise ValueError("Evidence set not found")

    evidence = []

    for index, item in enumerate(
        evidence_set.items,
        start=1,
    ):
        item_response = build_evidence_item_response(
            item,
            db,
        )

        evidence.append(
            AIContextEvidence(
                evidence_number=index,
                result_type=item_response.result_type,
                reference=item_response.reference,

                title=item_response.title,
                collection=item_response.collection,
                book_number=item_response.book_number,
                book_name=item_response.book_name,
                narrator=item_response.narrator,

                text_arabic=item_response.text_arabic,
                translation=item_response.translation,
                translator=item_response.translator,

                source_name=item_response.source.name,
                source_author=item_response.source.author,
                source_publisher=item_response.source.publisher,
                source_url=item_response.source.url,
                source_license=item_response.source.license,
                source_version=item_response.source.version,
                source_provenance=(
                    item_response.source.provenance_note
                ),
            )
        )

    return AIContextResponse(
        question=evidence_set.query,
        evidence=evidence,
    )