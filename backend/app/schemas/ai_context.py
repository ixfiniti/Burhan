from pydantic import BaseModel


class AIContextEvidence(BaseModel):
    evidence_number: int

    result_type: str
    reference: str

    title: str | None
    collection: str | None
    book_number: int | None
    book_name: str | None
    narrator: str | None

    text_arabic: str
    translation: str | None
    translator: str | None

    source_name: str
    source_author: str | None
    source_publisher: str | None
    source_url: str | None
    source_license: str | None
    source_version: str | None
    source_provenance: str | None


class AIContextResponse(BaseModel):
    question: str
    evidence: list[AIContextEvidence]