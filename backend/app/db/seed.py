from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Source


def seed_sources():
    db = SessionLocal()

    try:
        existing = db.scalar(
            select(Source).where(Source.slug == "quran")
        )

        if existing:
            print("Qur'an source already exists.")
            return

        quran = Source(
            name="The Qur'an",
            slug="quran",
            source_type="quran",
            language="ar",
            author=None,
            publisher=None,
            description="The Qur'an, the central scripture of Islam.",
        )

        db.add(quran)
        db.commit()

        print("Qur'an source created.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_sources()