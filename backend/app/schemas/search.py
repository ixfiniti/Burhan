from pydantic import BaseModel


class SearchSourceResponse(BaseModel):
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
    description: str | None


class SearchResult(BaseModel):
    surah_number: int
    surah_name: str
    ayah_number: int
    reference: str

    text_arabic: str

    translation: str
    translator: str

    source: SearchSourceResponse

    score: float