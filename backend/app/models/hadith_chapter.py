from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hadith_book import HadithBook
    from app.models.hadith import Hadith


class HadithChapter(Base):
    __tablename__ = "hadith_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)

    book_id: Mapped[int] = mapped_column(
        ForeignKey("hadith_books.id"),
        nullable=False,
    )

    number: Mapped[int] = mapped_column(
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    book: Mapped["HadithBook"] = relationship(
        back_populates="chapters",
    )

    hadiths: Mapped[list["Hadith"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
    )