from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.session import SessionLocal
from app.models.surah import Surah
from app.models.ayah import Ayah
from app.models.translation import Translation
from app.schemas.ayah import (
    AyahResponse,
    AyahWithTranslationsResponse,
    SurahWithAyahsResponse,
)
from app.schemas.surah import SurahResponse


router = APIRouter(
    prefix="/surahs",
    tags=["Surahs"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_surahs(db: Session = Depends(get_db)):
    return db.query(Surah).order_by(Surah.number).all()


@router.get(
    "/{surah_id}",
    response_model=SurahResponse,
)
def get_surah(
    surah_id: int,
    db: Session = Depends(get_db),
):
    surah = (
        db.query(Surah)
        .filter(Surah.number == surah_id)
        .first()
    )

    if surah is None:
        raise HTTPException(
            status_code=404,
            detail="Surah not found",
        )

    return surah


@router.get(
    "/{surah_id}/ayahs/",
    response_model=list[AyahResponse],
)
def list_ayahs(
    surah_id: int,
    db: Session = Depends(get_db),
):
    surah = (
        db.query(Surah)
        .filter(Surah.number == surah_id)
        .first()
    )

    if surah is None:
        raise HTTPException(
            status_code=404,
            detail="Surah not found",
        )

    return (
        db.query(Ayah)
        .filter(Ayah.surah_id == surah.id)
        .order_by(Ayah.number)
        .all()
    )


@router.get(
    "/{surah_id}/ayahs-with-translations",
    response_model=SurahWithAyahsResponse,
)
def get_surah_with_translations(
    surah_id: int,
    db: Session = Depends(get_db),
):
    surah = (
        db.query(Surah)
        .filter(Surah.number == surah_id)
        .first()
    )

    if surah is None:
        raise HTTPException(
            status_code=404,
            detail="Surah not found",
        )

    ayahs = (
        db.query(Ayah)
        .filter(Ayah.surah_id == surah.id)
        .order_by(Ayah.number)
        .all()
    )

    ayah_ids = [ayah.id for ayah in ayahs]

    translations = (
        db.query(Translation)
        .options(joinedload(Translation.source))
        .filter(Translation.ayah_id.in_(ayah_ids))
        .order_by(
            Translation.ayah_id,
            Translation.translator,
        )
        .all()
        if ayah_ids
        else []
    )

    translations_by_ayah = {}

    for translation in translations:
        translations_by_ayah.setdefault(
            translation.ayah_id,
            [],
        ).append(translation)

    return {
        "surah": {
            "id": surah.id,
            "number": surah.number,
            "name_arabic": surah.name_arabic,
            "name_transliteration": surah.name_transliteration,
            "name_english": surah.name_english,
        },
        "ayahs": [
            {
                "number": ayah.number,
                "text_arabic": ayah.text_arabic,
                "translations": [
                    {
                        "id": translation.id,
                        "language": translation.language,
                        "translator": translation.translator,
                        "text": translation.text,
                        "source": {
                            "id": translation.source.id,
                            "name": translation.source.name,
                            "slug": translation.source.slug,
                            "source_type": translation.source.source_type,
                            "language": translation.source.language,
                            "author": translation.source.author,
                            "publisher": translation.source.publisher,
                            "url": translation.source.url,
                            "license": translation.source.license,
                            "version": translation.source.version,
                            "description": translation.source.description,
                        },
                    }
                    for translation in translations_by_ayah.get(
                        ayah.id,
                        [],
                    )
                ],
            }
            for ayah in ayahs
        ],
    }


@router.get(
    "/{surah_id}/ayahs/{ayah_number}",
    response_model=AyahWithTranslationsResponse,
)
def get_ayah(
    surah_id: int,
    ayah_number: int,
    db: Session = Depends(get_db),
):
    surah = (
        db.query(Surah)
        .filter(Surah.number == surah_id)
        .first()
    )

    if surah is None:
        raise HTTPException(
            status_code=404,
            detail="Surah not found",
        )

    ayah = (
        db.query(Ayah)
        .filter(
            Ayah.surah_id == surah.id,
            Ayah.number == ayah_number,
        )
        .first()
    )

    if ayah is None:
        raise HTTPException(
            status_code=404,
            detail="Ayah not found",
        )

    translations = (
        db.query(Translation)
        .options(joinedload(Translation.source))
        .filter(Translation.ayah_id == ayah.id)
        .all()
    )

    return {
        "surah": {
            "id": surah.id,
            "number": surah.number,
            "name_arabic": surah.name_arabic,
            "name_transliteration": surah.name_transliteration,
            "name_english": surah.name_english,
        },
        "ayah": {
            "id": ayah.id,
            "number": ayah.number,
            "text_arabic": ayah.text_arabic,
        },
        "translations": [
            {
                "id": translation.id,
                "language": translation.language,
                "translator": translation.translator,
                "text": translation.text,
                "source": {
                    "id": translation.source.id,
                    "name": translation.source.name,
                    "slug": translation.source.slug,
                    "source_type": translation.source.source_type,
                    "language": translation.source.language,
                    "author": translation.source.author,
                    "publisher": translation.source.publisher,
                    "url": translation.source.url,
                    "license": translation.source.license,
                    "version": translation.source.version,
                    "description": translation.source.description,
                },
            }
            for translation in translations
        ],
    }