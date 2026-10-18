
import sqlite3

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.hadith_collection import HadithCollection
from app.models.hadith_book import HadithBook
from app.models.hadith_chapter import HadithChapter
from app.models.hadith import Hadith
from app.models.hadith_translation import HadithTranslation


SQLITE_PATH = r"data\hadith\hadiths.db"


def get_or_create_collection(db: Session) -> HadithCollection:
    collection = (
        db.query(HadithCollection)
        .filter(HadithCollection.slug == "sahih-al-bukhari")
        .first()
    )

    if collection is None:
        collection = HadithCollection(
            name="Sahih al-Bukhari",
            slug="sahih-al-bukhari",
            language="ar",
            author="Imam Bukhari",
            description="Sahih al-Bukhari hadith collection.",
        )
        db.add(collection)
        db.flush()

    return collection


def import_bukhari() -> None:
    sqlite_db = sqlite3.connect(SQLITE_PATH)
    sqlite_db.row_factory = sqlite3.Row

    db = SessionLocal()

    try:
        collection = get_or_create_collection(db)

        books = {}
        chapters = {}

        for row in sqlite_db.execute("""
            SELECT *
            FROM books
            WHERE collection_id = 'bukhari'
            ORDER BY book_number
        """):
            book = (
                db.query(HadithBook)
                .filter(
                    HadithBook.collection_id == collection.id,
                    HadithBook.number == int(row["book_number"]),
                )
                .first()
            )

            if book is None:
                book = HadithBook(
                    collection_id=collection.id,
                    number=int(row["book_number"]),
                    name=row["name_en"],
                    description=row["name_ar"],
                )
                db.add(book)
                db.flush()

            books[row["id"]] = book

        for row in sqlite_db.execute("""
            SELECT *
            FROM chapters
            WHERE book_id IN (
                SELECT id
                FROM books
                WHERE collection_id = 'bukhari'
            )
            ORDER BY book_id, chapter_number
        """):
            book = books[row["book_id"]]

            chapter = (
                db.query(HadithChapter)
                .filter(
                    HadithChapter.book_id == book.id,
                    HadithChapter.number == int(row["chapter_number"]),
                )
                .first()
            )

            if chapter is None:
                chapter = HadithChapter(
                    book_id=book.id,
                    number=int(row["chapter_number"]),
                    name=row["name_en"],
                    description=row["name_ar"],
                )
                db.add(chapter)
                db.flush()

            chapters[
                (row["book_id"], int(row["chapter_number"]))
            ] = chapter

        hadith_count = 0
        translation_count = 0

        for row in sqlite_db.execute("""
            SELECT *
            FROM hadiths
            WHERE collection_id = 'bukhari'
            ORDER BY id
        """):
            book = books[row["book_id"]]

            existing = (
                db.query(Hadith)
                .filter(Hadith.reference == row["reference"])
                .first()
            )

            if existing is None:
                chapter = None

                if row["chapter_number"] is not None:
                    chapter = chapters.get(
                        (
                            row["book_id"],
                            int(row["chapter_number"]),
                        )
                    )

                hadith = Hadith(
                    book_id=book.id,
                    chapter_id=chapter.id if chapter else None,
                    number=str(row["hadith_number"]),
                    reference=row["reference"],
                    in_book_reference=row["in_book_reference"],
                    text_arabic=row["text_ar"],
                    isnad_arabic=row["isnad_ar"],
                    matn_arabic=row["matn_ar"],
                    closing_arabic=row["closing_ar"],
                    narrator=row["narrator"],
                    has_variants=bool(row["has_variants"]),
                    source_reference=row["source_reference"],
                    source_url=row["url_source"],
                )

                db.add(hadith)
                db.flush()

                hadith_count += 1
            else:
                hadith = existing

            if row["text_en"]:
                existing_translation = (
                    db.query(HadithTranslation)
                    .filter(
                        HadithTranslation.hadith_id == hadith.id,
                        HadithTranslation.language == "en",
                        HadithTranslation.translator == "Sunnah.com",
                    )
                    .first()
                )

                if existing_translation is None:
                    db.add(
                        HadithTranslation(
                            hadith_id=hadith.id,
                            language="en",
                            translator="Sunnah.com",
                            text=row["text_en"],
                        )
                    )
                    translation_count += 1

        db.commit()

        print(f"Imported/updated collection: {collection.name}")
        print(f"Books available: {len(books)}")
        print(f"Chapters available: {len(chapters)}")
        print(f"New hadiths imported: {hadith_count}")
        print(f"New English translations imported: {translation_count}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        sqlite_db.close()


if __name__ == "__main__":
    import_bukhari()
