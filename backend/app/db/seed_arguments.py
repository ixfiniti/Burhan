from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.argument_category import ArgumentCategory


CATEGORIES = [
    {
        "name": "Islamic Questions",
        "slug": "islamic-questions",
        "description": (
            "Questions concerning the Qur'an, Sunnah, Islamic law, "
            "interpretation, worship, and religious practice."
        ),
    },
    {
        "name": "Theology",
        "slug": "theology",
        "description": (
            "Questions concerning God, divine attributes, revelation, "
            "free will, evil, and theological reasoning."
        ),
    },
    {
        "name": "Metaphysics & Philosophy",
        "slug": "metaphysics",
        "description": (
            "Philosophical questions concerning existence, causation, "
            "necessity, consciousness, identity, and related subjects."
        ),
    },
    {
        "name": "Epistemology",
        "slug": "epistemology",
        "description": (
            "Questions concerning knowledge, reason, revelation, "
            "certainty, justification, and evidence."
        ),
    },
    {
        "name": "Ethics",
        "slug": "ethics",
        "description": (
            "Questions concerning morality, moral obligation, "
            "good and evil, virtue, and moral reasoning."
        ),
    },
]


def seed_categories() -> None:
    db = SessionLocal()

    try:
        for category_data in CATEGORIES:
            existing = db.scalar(
                select(ArgumentCategory).where(
                    ArgumentCategory.slug == category_data["slug"]
                )
            )

            if existing:
                continue

            db.add(ArgumentCategory(**category_data))

        db.commit()
        print("Argument categories seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()