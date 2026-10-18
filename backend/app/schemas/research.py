
from pydantic import BaseModel


class ResearchSourceResponse(BaseModel):

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


class ResearchResult(BaseModel):

    id: int

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

    match_type: str

    source: ResearchSourceResponse
    primary_source: ResearchSourceResponse | None
    translation_source: ResearchSourceResponse | None

    score: float

    evidence_role: str


class ResearchResponse(BaseModel):

    results: list[ResearchResult]

    total: int

    limit: int

    offset: int

    has_more: bool
