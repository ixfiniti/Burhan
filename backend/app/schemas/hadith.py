from pydantic import BaseModel


class HadithSourceResponse(BaseModel):
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


class HadithTranslationResponse(BaseModel):
    id: int
    language: str
    translator: str
    text: str


class HadithGradingResponse(BaseModel):
    id: int
    scholar: str
    grade: str
    notes: str | None


class HadithBookResponse(BaseModel):
    id: int
    number: int
    name: str
    description: str | None


class HadithChapterResponse(BaseModel):
    id: int
    number: int
    name: str | None
    description: str | None


class HadithResponse(BaseModel):
    id: int

    number: str
    reference: str
    in_book_reference: str | None

    text_arabic: str
    isnad_arabic: str | None
    matn_arabic: str | None
    closing_arabic: str | None

    narrator: str | None
    has_variants: bool

    source_reference: str | None
    source_url: str | None

    collection_name: str
    book: HadithBookResponse
    chapter: HadithChapterResponse | None

    translations: list[HadithTranslationResponse]
    gradings: list[HadithGradingResponse]

    source: HadithSourceResponse