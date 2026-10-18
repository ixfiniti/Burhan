from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.source import Source
from app.schemas.document import DocumentCreate


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()


@router.post("/")
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
):
    source = db.get(Source, document.source_id)

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found",
        )

    new_document = Document(
        source_id=document.source_id,
        title=document.title,
        document_type=document.document_type,
        reference=document.reference,
        language=document.language,
        text=document.text,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted",
        "id": document_id,
    }