from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.hadith_collection import HadithCollection
    from app.models.hadith_chapter import HadithChapter


class HadithBook(Base):
    __tablename__ = "hadith_books"

    id: Mapped[int] = mapped_column(primary_key=True)

    collection_id: Mapped[int] = mapped_column(
        ForeignKey("hadith_collections.id"),
        nullable=False,
    )

    number: Mapped[int] = mapped_column(
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    collection: Mapped["HadithCollection"] = relationship(
        back_populates="books",
    )

    chapters: Mapped[list["HadithChapter"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )