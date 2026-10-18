"""
debug_search.py

TEMPORARY, READ-ONLY diagnostic script for the Burhan English
multi-term retrieval bug.

This script:
  - performs SELECT-only queries
  - never INSERTs / UPDATEs / DELETEs
  - never calls db.commit()
  - never modifies research.py or any project file
  - never modifies the database

Run with:

    python debug_search.py

from D:\\Burhan\\backend
"""

import importlib
import inspect

from sqlalchemy import func

# ---------------------------------------------------------
# Import the ACTUAL running module + session factory
# ---------------------------------------------------------

research_module = importlib.import_module("app.api.research")

from app.db.session import SessionLocal
from app.models.ayah import Ayah
from app.models.surah import Surah
from app.models.translation import Translation
from app.models.source import Source
from app.models.hadith import Hadith
from app.models.hadith_book import HadithBook
from app.models.hadith_collection import HadithCollection
from app.models.hadith_translation import HadithTranslation

expand_search_terms = research_module.expand_search_terms
_english_retrieval_variants = research_module._english_retrieval_variants
expanded_english_tsquery = research_module.expanded_english_tsquery
expanded_english_rank = research_module.expanded_english_rank


TEST_QUERIES = [
    "punishment",
    "zina",
    "punishment zina",
    "what is the punishment for zina",
]

MULTI_TERM_QUERIES = {
    "punishment zina",
    "what is the punishment for zina",
}


def section(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def show_sample_translations(rows, label, max_rows=5):
    print(f"    -- sample {label} (up to {max_rows}) --")
    if not rows:
        print("    (none)")
        return
    for row in rows[:max_rows]:
        # row is expected to be a Translation or HadithTranslation instance
        snippet = (row.text or "")[:100].replace("\n", " ")
        print(f"    id={row.id!r}  text={snippet!r}")


def main():
    print("BURHAN SEARCH DIAGNOSTIC (READ-ONLY)")
    print(research_module.__file__)

    section("SOURCE: expand_search_terms")
    print(inspect.getsource(expand_search_terms))

    section("SOURCE: _english_retrieval_variants")
    print(inspect.getsource(_english_retrieval_variants))

    section("SOURCE: expanded_english_tsquery")
    print(inspect.getsource(expanded_english_tsquery))

    section("SOURCE: expanded_english_rank")
    print(inspect.getsource(expanded_english_rank))

    db = SessionLocal()

    try:
        for query in TEST_QUERIES:
            section(f"QUERY: {query!r}")

            terms = expand_search_terms(query)
            print(f"expand_search_terms(query) -> {terms!r}")

            variants = _english_retrieval_variants(terms)
            print(f"_english_retrieval_variants(terms) -> {variants!r}")

            # -----------------------------------------------------
            # Qur'an: FTS-only count (no language filter, no joins)
            # -----------------------------------------------------

            quran_match_expr = expanded_english_tsquery(
                Translation.text, terms
            )

            quran_fts_only_q = db.query(func.count(Translation.id)).filter(
                quran_match_expr
            )
            quran_fts_only_count = quran_fts_only_q.scalar()
            print(f"[Quran]  FTS-only match count: {quran_fts_only_count}")

            quran_fts_sample = (
                db.query(Translation)
                .filter(quran_match_expr)
                .limit(5)
                .all()
            )
            show_sample_translations(quran_fts_sample, "Quran FTS-only matches")

            # -----------------------------------------------------
            # Qur'an: FTS + language == 'en'
            # -----------------------------------------------------

            quran_fts_lang_q = (
                db.query(func.count(Translation.id))
                .filter(Translation.language == "en")
                .filter(quran_match_expr)
            )
            quran_fts_lang_count = quran_fts_lang_q.scalar()
            print(f"[Quran]  FTS + language='en' count: {quran_fts_lang_count}")

            # -----------------------------------------------------
            # Qur'an: full join chain, matching research_search()
            # -----------------------------------------------------

            quran_rank_expr = expanded_english_rank(Translation.text, terms)

            quran_full_query = (
                db.query(
                    Ayah,
                    Surah,
                    Translation,
                    Source,
                    quran_rank_expr.label("english_score"),
                )
                .join(Surah, Ayah.surah_id == Surah.id)
                .join(Translation, Translation.ayah_id == Ayah.id)
                .join(Source, Translation.source_id == Source.id)
                .filter(Translation.language == "en")
                .filter(quran_match_expr)
            )

            quran_full_count = quran_full_query.count()
            print(f"[Quran]  FULL retrieval (same joins as research_search): {quran_full_count}")

            if quran_full_count:
                sample_rows = quran_full_query.limit(5).all()
                print("    -- sample full-chain Quran matches --")
                for ayah, surah, translation, source, score in sample_rows:
                    snippet = (translation.text or "")[:100].replace("\n", " ")
                    print(
                        f"    ayah_id={ayah.id} surah={surah.number} "
                        f"score={score} text={snippet!r}"
                    )

            # -----------------------------------------------------
            # Hadith: FTS-only count
            # -----------------------------------------------------

            hadith_match_expr = expanded_english_tsquery(
                HadithTranslation.text, terms
            )

            hadith_fts_only_count = (
                db.query(func.count(HadithTranslation.id))
                .filter(hadith_match_expr)
                .scalar()
            )
            print(f"[Hadith] FTS-only match count: {hadith_fts_only_count}")

            hadith_fts_sample = (
                db.query(HadithTranslation)
                .filter(hadith_match_expr)
                .limit(5)
                .all()
            )
            show_sample_translations(hadith_fts_sample, "Hadith FTS-only matches")

            # -----------------------------------------------------
            # Hadith: FTS + language == 'en'
            # -----------------------------------------------------

            hadith_fts_lang_count = (
                db.query(func.count(HadithTranslation.id))
                .filter(HadithTranslation.language == "en")
                .filter(hadith_match_expr)
                .scalar()
            )
            print(f"[Hadith] FTS + language='en' count: {hadith_fts_lang_count}")

            # -----------------------------------------------------
            # Hadith: full join chain, matching research_search()
            # -----------------------------------------------------

            hadith_rank_expr = expanded_english_rank(
                HadithTranslation.text, terms
            )

            hadith_full_query = (
                db.query(
                    Hadith,
                    HadithBook,
                    HadithCollection,
                    HadithTranslation,
                    Source,
                    hadith_rank_expr.label("english_score"),
                )
                .join(HadithBook, Hadith.book_id == HadithBook.id)
                .join(
                    HadithCollection,
                    HadithBook.collection_id == HadithCollection.id,
                )
                .outerjoin(
                    HadithTranslation,
                    (HadithTranslation.hadith_id == Hadith.id)
                    & (HadithTranslation.language == "en"),
                )
                .join(Source, HadithCollection.source_id == Source.id)
                .filter(hadith_match_expr)
            )

            hadith_full_count = hadith_full_query.count()
            print(f"[Hadith] FULL retrieval (same joins as research_search): {hadith_full_count}")

            if hadith_full_count:
                sample_rows = hadith_full_query.limit(5).all()
                print("    -- sample full-chain Hadith matches --")
                for hadith, book, collection, translation, source, score in sample_rows:
                    text = translation.text if translation else None
                    snippet = (text or "")[:100].replace("\n", " ")
                    print(
                        f"    hadith_id={hadith.id} book={book.number} "
                        f"score={score} translation_present={translation is not None} "
                        f"text={snippet!r}"
                    )

            # -----------------------------------------------------
            # Compiled SQL for the failing multi-term queries
            # -----------------------------------------------------

            if query in MULTI_TERM_QUERIES:
                section(f"COMPILED SQL (Quran) for: {query!r}")
                print(
                    quran_full_query.statement.compile(
                        compile_kwargs={"literal_binds": True}
                    )
                )

                section(f"COMPILED SQL (Hadith) for: {query!r}")
                print(
                    hadith_full_query.statement.compile(
                        compile_kwargs={"literal_binds": True}
                    )
                )

    finally:
        # Read-only session: nothing was added or modified.
        # No commit. Just close.
        db.close()

    print()
    print("========== DIAGNOSTIC COMPLETE ==========")


if __name__ == "__main__":
    main()
