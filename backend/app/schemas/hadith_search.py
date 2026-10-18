from pydantic import BaseModel


class HadithSearchResult(BaseModel):
    id: int
    number: str
    reference: str
    in_book_reference: str | None

    collection_name: str
    book_number: int | None
    book_name: str | None

    text_arabic: str
    translation: str | None
    translator: str | None

    narrator: str | None
    source_url: str | None

    score: float