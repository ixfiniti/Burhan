from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ayah import Ayah
    from app.models.source import Source


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True)

    ayah_id: Mapped[int] = mapped_column(
        ForeignKey("ayahs.id"),
        nullable=False,
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    translator: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    ayah: Mapped["Ayah"] = relationship()

    source: Mapped["Source"] = relationship()