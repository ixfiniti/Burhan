from pydantic import BaseModel


class TranslationSourceResponse(BaseModel):
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


class TranslationResponse(BaseModel):
    id: int
    language: str
    translator: str
    text: str
    source: TranslationSourceResponse