from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document import Document


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
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

    publisher: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    license: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    provenance_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )