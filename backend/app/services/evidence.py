from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ayah import Ayah
from app.models.hadith import Hadith
from app.models.hadith_book import HadithBook
from app.models.hadith_collection import HadithCollection
from app.models.hadith_translation import HadithTranslation
from app.models.source import Source
from app.models.surah import Surah
from app.models.translation import Translation


def build_source_data(source: Source | None) -> dict | None:
    if source is None:
        return None

    return {
        "id": source.id,
        "name": source.name,
        "slug": source.slug,
        "source_type": source.source_type,
        "language": source.language,
        "author": source.author,
        "publisher": source.publisher,
        "url": source.url,
        "license": source.license,
        "version": source.version,
        "provenance_note": source.provenance_note,
        "description": source.description,
    }


def get_source(
    source_id: int,
    db: Session,
) -> Source:
    source = (
        db.query(Source)
        .filter(Source.id == source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=500,
            detail=f"Source {source_id} not found",
        )

    return source


def resolve_evidence_result(
    result_type: str,
    result_id: int,
    source_id: int | None,
    db: Session,
) -> dict:
    stored_source = None

    if source_id is not None:
        stored_source = get_source(source_id, db)

    title = None
    collection = None
    book_number = None
    book_name = None
    narrator = None
    text_arabic = ""
    translation = None
    translator = None

    primary_source = stored_source
    translation_source = None

    if result_type == "quran":
        ayah = (
            db.query(Ayah)
            .filter(Ayah.id == result_id)
            .first()
        )

        if ayah is None:
            raise HTTPException(
                status_code=404,
                detail=f"Qur'an ayah {result_id} not found",
            )

        text_arabic = ayah.text_arabic

        surah = (
            db.query(Surah)
            .filter(Surah.id == ayah.surah_id)
            .first()
        )

        if surah is not None:
            title = surah.name_english

        quran_source = (
            db.query(Source)
            .filter(Source.source_type == "quran")
            .first()
        )

        if quran_source is not None:
            primary_source = quran_source

        translation_row = (
            db.query(Translation)
            .filter(Translation.ayah_id == ayah.id)
            .filter(Translation.language == "en")
            .first()
        )

        if translation_row is not None:
            translation = translation_row.text
            translator = translation_row.translator

            translation_source = (
                db.query(Source)
                .filter(Source.id == translation_row.source_id)
                .first()
            )

    elif result_type == "hadith":
        hadith = (
            db.query(Hadith)
            .filter(Hadith.id == result_id)
            .first()
        )

        if hadith is None:
            raise HTTPException(
                status_code=404,
                detail=f"Hadith {result_id} not found",
            )

        text_arabic = hadith.text_arabic
        narrator = hadith.narrator

        book = (
            db.query(HadithBook)
            .filter(HadithBook.id == hadith.book_id)
            .first()
        )

        if book is not None:
            book_number = book.number
            book_name = book.name
            title = book.name

            collection_row = (
                db.query(HadithCollection)
                .filter(
                    HadithCollection.id == book.collection_id
                )
                .first()
            )

            if collection_row is not None:
                collection = collection_row.name

                collection_source = (
                    db.query(Source)
                    .filter(
                        Source.id == collection_row.source_id
                    )
                    .first()
                )

                if collection_source is not None:
                    primary_source = collection_source

        translation_row = (
            db.query(HadithTranslation)
            .filter(
                HadithTranslation.hadith_id == hadith.id
            )
            .filter(
                HadithTranslation.language == "en"
            )
            .first()
        )

        if translation_row is not None:
            translation = translation_row.text
            translator = translation_row.translator
            translation_source = None

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported evidence result type: "
                f"{result_type}"
            ),
        )

    return {
        "title": title,
        "collection": collection,
        "book_number": book_number,
        "book_name": book_name,
        "narrator": narrator,
        "text_arabic": text_arabic,
        "translation": translation,
        "translator": translator,
        "source": build_source_data(stored_source),
        "primary_source": build_source_data(primary_source),
        "translation_source": build_source_data(
            translation_source
        ),
    }
