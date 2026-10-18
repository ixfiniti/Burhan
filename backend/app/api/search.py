
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ayah import Ayah
from app.models.surah import Surah
from app.models.translation import Translation
from app.models.source import Source
from app.schemas.search import SearchResult
from app.services.arabic import normalize_arabic


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# English relevance scoring
# ---------------------------------------------------------

def english_relevance_score(
    query: str,
    text: str | None,
) -> float:
    """
    Score English evidence based on actual lexical relevance.

    Exact phrases and complete query-term coverage receive the
    strongest scores. Partial/incidental matches receive lower scores.
    """

    if not text:
        return 0.0

    normalized_query = re.sub(
        r"\s+",
        " ",
        query.lower(),
    ).strip()

    normalized_text = re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()

    if not normalized_query or not normalized_text:
        return 0.0

    # Remove common question words that do not describe the subject.
    stop_words = {
        "what",
        "does",
        "do",
        "did",
        "is",
        "are",
        "was",
        "were",
        "the",
        "a",
        "an",
        "about",
        "say",
        "says",
        "tell",
        "me",
        "of",
        "in",
        "on",
        "for",
        "to",
        "and",
        "or",
        "how",
        "why",
        "who",
        "which",
    }

    query_tokens = [
        token
        for token in re.findall(
            r"\b[a-z0-9']+\b",
            normalized_query,
        )
        if token not in stop_words
    ]

    if not query_tokens:
        return 0.0

    text_tokens = set(
        re.findall(
            r"\b[a-z0-9']+\b",
            normalized_text,
        )
    )

    # Exact phrase.
    if normalized_query in normalized_text:
        return 1.0

    matched_tokens = sum(
        token in text_tokens
        for token in query_tokens
    )

    coverage = matched_tokens / len(query_tokens)

    # Every meaningful query term occurs.
    if coverage == 1.0:
        return 0.92

    # Most meaningful terms occur.
    if coverage >= 0.75:
        return 0.82

    # At least half occur.
    if coverage >= 0.50:
        return 0.68

    # Only one meaningful term occurs.
    if matched_tokens > 0:
        return 0.48

    return 0.0


# ---------------------------------------------------------
# Qur'an search
# ---------------------------------------------------------

@router.get(
    "/",
    response_model=list[SearchResult],
)
def search_quran(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    normalized_arabic_query = normalize_arabic(q)

    english_query = func.plainto_tsquery(
        "english",
        q,
    )

    english_vector = func.to_tsvector(
        "english",
        Translation.text,
    )

    english_match = english_vector.op("@@")(
        english_query
    )

    english_rank = func.ts_rank_cd(
        english_vector,
        english_query,
    )

    arabic_text_normalized = func.regexp_replace(
        Ayah.text_arabic,
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]",
        "",
        "g",
    )

    arabic_match = arabic_text_normalized.ilike(
        f"%{normalized_arabic_query}%"
    )

    arabic_exact_match = case(
        (
            arabic_text_normalized.ilike(
                f"%{normalized_arabic_query}%"
            ),
            1.0,
        ),
        else_=0.0,
    )

    combined_score = func.greatest(
        english_rank,
        arabic_exact_match,
    )

    results = (
        db.query(
            Surah.number.label("surah_number"),
            Surah.name_transliteration.label(
                "surah_name"
            ),
            Ayah.number.label("ayah_number"),
            func.concat(
                Surah.number,
                ":",
                Ayah.number,
            ).label("reference"),
            Ayah.text_arabic,
            Translation.text.label("translation"),
            Translation.translator,
            Source.id.label("source_id"),
            Source.name.label("source_name"),
            Source.slug.label("source_slug"),
            Source.source_type.label("source_type"),
            Source.language.label("source_language"),
            Source.author.label("source_author"),
            Source.publisher.label("source_publisher"),
            Source.url.label("source_url"),
            Source.license.label("source_license"),
            Source.version.label("source_version"),
            Source.description.label("source_description"),
            combined_score.label("score"),
        )
        .join(
            Ayah,
            Ayah.surah_id == Surah.id,
        )
        .join(
            Translation,
            Translation.ayah_id == Ayah.id,
        )
        .join(
            Source,
            Translation.source_id == Source.id,
        )
        .filter(
            Translation.language == "en",
            english_match | arabic_match,
        )
        .order_by(
            combined_score.desc(),
            Surah.number,
            Ayah.number,
        )
        .limit(limit)
        .all()
    )

    final_results = []

    for result in results:
        # ---------------------------------------------------------
        # Calculate actual translation relevance in Python.
        # ---------------------------------------------------------

        translation_score = english_relevance_score(
            q,
            result.translation,
        )

        # Arabic queries should rely on Arabic matching.
        is_arabic_query = bool(
            re.search(
                r"[\u0600-\u06FF]",
                q,
            )
        )

        arabic_score = (
            float(result.score or 0.0)
            if is_arabic_query
            else 0.0
        )

        score = max(
    translation_score,
    arabic_score,
)

        final_results.append(
            {
                "surah_number": result.surah_number,
                "surah_name": result.surah_name,
                "ayah_number": result.ayah_number,
                "reference": result.reference,
                "text_arabic": result.text_arabic,
                "translation": result.translation,
                "translator": result.translator,
                "source": {
                    "id": result.source_id,
                    "name": result.source_name,
                    "slug": result.source_slug,
                    "source_type": result.source_type,
                    "language": result.source_language,
                    "author": result.source_author,
                    "publisher": result.source_publisher,
                    "url": result.source_url,
                    "license": result.source_license,
                    "version": result.source_version,
                    "description": result.source_description,
                },
                "score": score,
            }
        )

    # ---------------------------------------------------------
    # Re-rank using the improved relevance score.
    # ---------------------------------------------------------

    final_results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    return final_results[:limit]
