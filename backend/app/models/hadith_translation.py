from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.hadith import Hadith


class HadithTranslation(Base):
    __tablename__ = "hadith_translations"

    id: Mapped[int] = mapped_column(primary_key=True)

    hadith_id: Mapped[int] = mapped_column(
        ForeignKey("hadiths.id"),
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

    hadith: Mapped["Hadith"] = relationship(
        back_populates="translations",
    )