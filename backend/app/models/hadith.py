from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hadith_book import HadithBook
    from app.models.hadith_chapter import HadithChapter
    from app.models.hadith_translation import HadithTranslation
    from app.models.hadith_grading import HadithGrading


class Hadith(Base):
    __tablename__ = "hadiths"

    id: Mapped[int] = mapped_column(primary_key=True)

    book_id: Mapped[int] = mapped_column(
        ForeignKey("hadith_books.id"),
        nullable=False,
    )

    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("hadith_chapters.id"),
        nullable=True,
    )

    number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    in_book_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    text_arabic: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    isnad_arabic: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    matn_arabic: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    closing_arabic: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    narrator: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    has_variants: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    book: Mapped["HadithBook"] = relationship()

    chapter: Mapped["HadithChapter | None"] = relationship(
        back_populates="hadiths",
    )

    translations: Mapped[list["HadithTranslation"]] = relationship(
        back_populates="hadith",
        cascade="all, delete-orphan",
    )

    gradings: Mapped[list["HadithGrading"]] = relationship(
        back_populates="hadith",
        cascade="all, delete-orphan",
    )