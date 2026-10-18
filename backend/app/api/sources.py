from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.source import Source
from app.schemas.source import SourceCreate
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()


@router.post("/")
def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db),
):
    new_source = Source(
        name=source.name,
        slug=source.slug,
        source_type=source.source_type,
        language=source.language,
        author=source.author,
        publisher=source.publisher,
        description=source.description,
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source

@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    source = db.get(Source, source_id)

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found",
        )

    db.delete(source)
    db.commit()

    return {
        "message": "Source deleted",
        "id": source_id,
    }