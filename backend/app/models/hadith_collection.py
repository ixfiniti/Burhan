from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hadith_book import HadithBook
    from app.models.source import Source


class HadithCollection(Base):
    __tablename__ = "hadith_collections"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    author: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped["Source"] = relationship()

    books: Mapped[list["HadithBook"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
    )