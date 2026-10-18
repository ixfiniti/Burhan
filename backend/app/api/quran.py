from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, select

from app.db.session import SessionLocal
from app.models.ayah import Ayah
from app.models.surah import Surah
from app.models.translation import Translation
from app.schemas.ayah import AyahWithTranslationsResponse
from app.models.translation import Translation
from app.services.arabic import normalize_arabic

router = APIRouter(
    prefix="/quran",
    tags=["Quran"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def search_quran(
    q: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    normalized_query = normalize_arabic(q.strip())
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    if not normalized_query:
        return []

    arabic_text = func.translate(
        func.regexp_replace(
            Ayah.text_arabic,
            "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]",
            "",
            "g",
        ),
        "أإآٱى",
        "ااااي",
    )

    english_match = (
        select(Translation.id)
        .where(
            Translation.ayah_id == Ayah.id,
            Translation.language == "en",
            Translation.text.ilike(f"%{normalized_query}%"),
        )
        .correlate(Ayah)
        .exists()
    )

    translation_text = (
        select(Translation.text)
        .where(
            Translation.ayah_id == Ayah.id,
            Translation.language == "en",
        )
        .order_by(Translation.id)
        .limit(1)
        .correlate(Ayah)
        .scalar_subquery()
    )

    translation_translator = (
        select(Translation.translator)
        .where(
            Translation.ayah_id == Ayah.id,
            Translation.language == "en",
        )
        .order_by(Translation.id)
        .limit(1)
        .correlate(Ayah)
        .scalar_subquery()
    )

    rows = (
        db.query(
            Ayah,
            Surah,
            translation_text.label("translation"),
            translation_translator.label("translator"),
        )
        .join(Surah, Ayah.surah_id == Surah.id)
        .filter(
            or_(
                arabic_text.ilike(
                    f"%{normalized_query}%"
                ),
                english_match,
            )
        )
        .order_by(
            Surah.number,
            Ayah.number,
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": ayah.id,
            "reference": f"{surah.number}:{ayah.number}",
            "surah_id": surah.id,
            "surah_number": surah.number,
            "surah_name_arabic": surah.name_arabic,
            "surah_name_english": surah.name_english,
            "surah_name_transliteration": (
                surah.name_transliteration
            ),
            "ayah_number": ayah.number,
            "text_arabic": ayah.text_arabic,
            "translation": translation,
            "translator": translator,
        }
        for ayah, surah, translation, translator in rows
    ]


@router.get(
    "/{ayah_id}",
    response_model=AyahWithTranslationsResponse,
)
def get_quran_ayah(
    ayah_id: int,
    db: Session = Depends(get_db),
):
    ayah = db.query(Ayah).filter(Ayah.id == ayah_id).first()

    if ayah is None:
        raise HTTPException(
            status_code=404,
            detail="Ayah not found",
        )

    surah = db.query(Surah).filter(Surah.id == ayah.surah_id).first()

    if surah is None:
        raise HTTPException(
            status_code=404,
            detail="Surah not found",
        )

    # 1. Fetch adjacent Ayahs in the same Surah
    previous_ayah = (
        db.query(Ayah)
        .filter(
            Ayah.surah_id == ayah.surah_id,
            Ayah.number == ayah.number - 1,
        )
        .first()
    )

    next_ayah = (
        db.query(Ayah)
        .filter(
            Ayah.surah_id == ayah.surah_id,
            Ayah.number == ayah.number + 1,
        )
        .first()
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
        # 2. Added navigation blocks at the bottom
        "previous": (
            {
                "id": previous_ayah.id,
                "number": previous_ayah.number,
                "reference": f"{surah.number}:{previous_ayah.number}",
            }
            if previous_ayah
            else None
        ),
        "next": (
            {
                "id": next_ayah.id,
                "number": next_ayah.number,
                "reference": f"{surah.number}:{next_ayah.number}",
            }
            if next_ayah
            else None
        ),
    }