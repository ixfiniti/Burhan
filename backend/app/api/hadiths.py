from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.hadith import Hadith
from app.models.hadith_book import HadithBook
from app.models.hadith_chapter import HadithChapter
from app.models.hadith_collection import HadithCollection
from app.models.hadith_translation import HadithTranslation
from app.models.hadith_grading import HadithGrading
from app.models.source import Source
from app.schemas.hadith import HadithResponse
from app.schemas.hadith_book import HadithBookResponse
from app.schemas.hadith_chapter import HadithChapterResponse
from app.schemas.hadith_collection import HadithCollectionResponse
from app.schemas.hadith_search import HadithSearchResult
from app.services.arabic import normalize_arabic


router = APIRouter(
    prefix="/hadiths",
    tags=["Hadith"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Collections
# ---------------------------------------------------------

@router.get(
    "/collections",
    response_model=list[HadithCollectionResponse],
)
def list_collections(
    db: Session = Depends(get_db),
):
    collections = (
        db.query(HadithCollection)
        .join(
            Source,
            HadithCollection.source_id == Source.id,
        )
        .order_by(HadithCollection.name)
        .all()
    )

    return [
        {
            "id": collection.id,
            "name": collection.name,
            "slug": collection.slug,
            "language": collection.language,
            "author": collection.author,
            "description": collection.description,
            "source": {
                "id": collection.source.id,
                "name": collection.source.name,
                "slug": collection.source.slug,
                "source_type": collection.source.source_type,
                "language": collection.source.language,
                "author": collection.source.author,
                "publisher": collection.source.publisher,
                "url": collection.source.url,
                "license": collection.source.license,
                "version": collection.source.version,
                "provenance_note": collection.source.provenance_note,
                "description": collection.source.description,
            },
        }
        for collection in collections
    ]


# ---------------------------------------------------------
# Books
# ---------------------------------------------------------

@router.get(
    "/collections/{collection_slug}/books",
    response_model=list[HadithBookResponse],
)
def list_books(
    collection_slug: str,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(HadithCollection)
        .filter(
            HadithCollection.slug == collection_slug
        )
        .first()
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith collection not found",
        )

    return (
        db.query(HadithBook)
        .filter(
            HadithBook.collection_id == collection.id
        )
        .order_by(HadithBook.number)
        .all()
    )


# ---------------------------------------------------------
# Chapters
# ---------------------------------------------------------

@router.get(
    "/collections/{collection_slug}/books/{book_number}/chapters",
    response_model=list[HadithChapterResponse],
)
def list_chapters(
    collection_slug: str,
    book_number: int,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(HadithCollection)
        .filter(
            HadithCollection.slug == collection_slug
        )
        .first()
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith collection not found",
        )

    book = (
        db.query(HadithBook)
        .filter(
            HadithBook.collection_id == collection.id,
            HadithBook.number == book_number,
        )
        .first()
    )

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith book not found",
        )

    return (
        db.query(HadithChapter)
        .filter(
            HadithChapter.book_id == book.id
        )
        .order_by(HadithChapter.number)
        .all()
    )


@router.get(
    "/collections/{collection_slug}/books/{book_number}/chapters/{chapter_number}",
    response_model=HadithChapterResponse,
)
def get_chapter(
    collection_slug: str,
    book_number: int,
    chapter_number: int,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(HadithCollection)
        .filter(
            HadithCollection.slug == collection_slug
        )
        .first()
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith collection not found",
        )

    book = (
        db.query(HadithBook)
        .filter(
            HadithBook.collection_id == collection.id,
            HadithBook.number == book_number,
        )
        .first()
    )

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith book not found",
        )

    chapter = (
        db.query(HadithChapter)
        .filter(
            HadithChapter.book_id == book.id,
            HadithChapter.number == chapter_number,
        )
        .first()
    )

    if chapter is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith chapter not found",
        )

    return chapter


# ---------------------------------------------------------
# Book Hadiths
# ---------------------------------------------------------

@router.get(
    "/collections/{collection_slug}/books/{book_number}/hadiths",
    response_model=list[HadithResponse],
)
def list_book_hadiths(
    collection_slug: str,
    book_number: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    collection = (
        db.query(HadithCollection)
        .filter(
            HadithCollection.slug == collection_slug
        )
        .first()
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith collection not found",
        )

    book = (
        db.query(HadithBook)
        .filter(
            HadithBook.collection_id == collection.id,
            HadithBook.number == book_number,
        )
        .first()
    )

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith book not found",
        )

    source = (
        db.query(Source)
        .filter(
            Source.id == collection.source_id
        )
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=500,
            detail="Hadith source not found",
        )

    hadiths = (
        db.query(Hadith)
        .filter(
            Hadith.book_id == book.id
        )
        .order_by(Hadith.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": hadith.id,
            "number": hadith.number,
            "reference": hadith.reference,
            "in_book_reference": hadith.in_book_reference,

            "text_arabic": hadith.text_arabic,
            "isnad_arabic": hadith.isnad_arabic,
            "matn_arabic": hadith.matn_arabic,
            "closing_arabic": hadith.closing_arabic,

            "narrator": hadith.narrator,
            "has_variants": hadith.has_variants,

            "source_reference": hadith.source_reference,
            "source_url": hadith.source_url,

            "source": {
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
            },

            "book": {
                "id": book.id,
                "number": book.number,
                "name": book.name,
                "description": book.description,
            },

            "chapter": (
                {
                    "id": hadith.chapter.id,
                    "number": hadith.chapter.number,
                    "name": hadith.chapter.name,
                    "description": hadith.chapter.description,
                }
                if hadith.chapter
                else None
            ),

            "translations": hadith.translations,
            "gradings": hadith.gradings,
        }
        for hadith in hadiths
    ]


# ---------------------------------------------------------
# Hadith Search
# ---------------------------------------------------------

@router.get(
    "/search",
    response_model=list[HadithSearchResult],
)
def search_hadiths(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    english_query = func.plainto_tsquery(
        "english",
        q,
    )

    english_vector = func.to_tsvector(
        "english",
        HadithTranslation.text,
    )

    english_match = english_vector.op("@@")(
        english_query
    )

    english_rank = func.ts_rank_cd(
        english_vector,
        english_query,
    )

    normalized_query = normalize_arabic(q)

    arabic_search_term = f"%{normalized_query}%"

    arabic_text_normalized = func.regexp_replace(
        Hadith.text_arabic,
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]",
        "",
        "g",
    )

    arabic_text_normalized = func.replace(
        arabic_text_normalized,
        "أ",
        "ا",
    )

    arabic_text_normalized = func.replace(
        arabic_text_normalized,
        "إ",
        "ا",
    )

    arabic_text_normalized = func.replace(
        arabic_text_normalized,
        "آ",
        "ا",
    )

    arabic_text_normalized = func.replace(
        arabic_text_normalized,
        "ٱ",
        "ا",
    )

    arabic_text_normalized = func.replace(
        arabic_text_normalized,
        "ى",
        "ي",
    )

    arabic_match = arabic_text_normalized.ilike(
        arabic_search_term
    )

    arabic_score = case(
        (arabic_match, 1.0),
        else_=0.0,
    )

    combined_score = func.greatest(
        english_rank,
        arabic_score,
    )

    rows = (
        db.query(
            Hadith,
            HadithBook,
            HadithCollection,
            HadithTranslation,
            combined_score.label("score"),
        )
        .join(
            HadithBook,
            Hadith.book_id == HadithBook.id,
        )
        .join(
            HadithCollection,
            HadithBook.collection_id == HadithCollection.id,
        )
        .outerjoin(
            HadithTranslation,
            (
                HadithTranslation.hadith_id == Hadith.id
            )
            & (
                HadithTranslation.language == "en"
            ),
        )
        .filter(
            or_(
                english_match,
                arabic_match,
            )
        )
        .order_by(
            combined_score.desc(),
            Hadith.id,
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []

    for (
        hadith,
        book,
        collection,
        translation,
        match_score,
    ) in rows:
        results.append(
            {
                "id": hadith.id,
                "number": hadith.number,
                "reference": hadith.reference,
                "in_book_reference": hadith.in_book_reference,

                "collection_name": collection.name,
                "book_number": book.number,
                "book_name": book.name,

                "text_arabic": hadith.text_arabic,
                "translation": (
                    translation.text
                    if translation
                    else None
                ),
                "translator": (
                    translation.translator
                    if translation
                    else None
                ),

                "narrator": hadith.narrator,
                "source_url": hadith.source_url,

                "score": float(match_score),
            }
        )

    return results


# ---------------------------------------------------------
# Individual Hadith Evidence
# ---------------------------------------------------------

@router.get(
    "/{hadith_id}",
    response_model=HadithResponse,
)
def get_hadith(
    hadith_id: int,
    db: Session = Depends(get_db),
):
    hadith = (
        db.query(Hadith)
        .filter(Hadith.id == hadith_id)
        .first()
    )

    if hadith is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith not found",
        )

    book = hadith.book

    if book is None:
        raise HTTPException(
            status_code=500,
            detail="Hadith book not found",
        )

    chapter = hadith.chapter

    collection = (
        db.query(HadithCollection)
        .filter(
            HadithCollection.id == book.collection_id
        )
        .first()
    )

    if collection is None:
        raise HTTPException(
            status_code=500,
            detail="Hadith collection not found",
        )

    source = (
        db.query(Source)
        .filter(
            Source.id == collection.source_id
        )
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=500,
            detail="Hadith source not found",
        )

    return {
        "id": hadith.id,

        "number": hadith.number,
        "reference": hadith.reference,
        "in_book_reference": hadith.in_book_reference,

        "text_arabic": hadith.text_arabic,
        "isnad_arabic": hadith.isnad_arabic,
        "matn_arabic": hadith.matn_arabic,
        "closing_arabic": hadith.closing_arabic,

        "narrator": hadith.narrator,
        "has_variants": hadith.has_variants,

        "source_reference": hadith.source_reference,
        "source_url": hadith.source_url,

        "collection_name": collection.name,

        "book": {
            "id": book.id,
            "number": book.number,
            "name": book.name,
            "description": book.description,
        },

        "chapter": (
            {
                "id": chapter.id,
                "number": chapter.number,
                "name": chapter.name,
                "description": chapter.description,
            }
            if chapter
            else None
        ),

        "translations": [
            {
                "id": translation.id,
                "language": translation.language,
                "translator": translation.translator,
                "text": translation.text,
            }
            for translation in hadith.translations
        ],

        "gradings": [
            {
                "id": grading.id,
                "scholar": grading.scholar,
                "grade": grading.grade,
                "notes": grading.notes,
            }
            for grading in hadith.gradings
        ],

        "source": {
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
        },
    }