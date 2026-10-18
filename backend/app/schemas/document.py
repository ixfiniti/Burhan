from pydantic import BaseModel


class DocumentCreate(BaseModel):
    source_id: int
    title: str
    document_type: str
    reference: str
    language: str
    text: str