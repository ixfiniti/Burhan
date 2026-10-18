
from datetime import datetime

from pydantic import BaseModel


class EvidenceItemCreate(BaseModel):
    result_type: str
    result_id: int
    reference: str
    source_id: int
    score: float


class EvidenceSourceResponse(BaseModel):
    id: int
    name: str
    slug: str
    source_type: str
    language: str
    author: str | None
    publisher: str | None
    url: str | None
    license: str | None
    version: str | None
    provenance_note: str | None
    description: str | None


class EvidenceItemResponse(BaseModel):
    id: int
    result_type: str
    result_id: int
    reference: str
    source_id: int
    score: float

    title: str | None
    collection: str | None
    book_number: int | None
    book_name: str | None
    narrator: str | None

    text_arabic: str
    translation: str | None
    translator: str | None

    # The source represented by the stored evidence item.
    source: EvidenceSourceResponse

    # The underlying primary textual source.
    primary_source: EvidenceSourceResponse

    # The source of the English translation, when known.
    translation_source: EvidenceSourceResponse | None


class EvidenceSetCreate(BaseModel):
    query: str
    items: list[EvidenceItemCreate]


class EvidenceSetResponse(BaseModel):
    id: int
    query: str
    created_at: datetime
    items: list[EvidenceItemResponse]
