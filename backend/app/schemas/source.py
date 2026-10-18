from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    slug: str
    source_type: str
    language: str
    author: str | None = None
    publisher: str | None = None
    description: str | None = None