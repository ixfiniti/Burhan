from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ayah import Ayah
from app.models.translation import Translation


router = APIRouter(
    prefix="/surahs",
    tags=["Translations"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{surah_id}/ayahs/{ayah_number}/translations")
def list_translations(
    surah_id: int,
    ayah_number: int,
    db: Session = Depends(get_db),
):
    ayah = (
        db.query(Ayah)
        .filter(
            Ayah.surah_id == surah_id,
            Ayah.number == ayah_number,
        )
        .first()
    )

    if ayah is None:
        raise HTTPException(
            status_code=404,
            detail="Ayah not found",
        )

    return (
        db.query(Translation)
        .filter(Translation.ayah_id == ayah.id)
        .all()
    )