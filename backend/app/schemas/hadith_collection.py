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


class HadithCollectionResponse(BaseModel):
    id: int
    name: str
    slug: str
    language: str
    author: str | None
    description: str | None
    source: HadithSourceResponse