from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.hadith import Hadith


class HadithGrading(Base):
    __tablename__ = "hadith_gradings"

    id: Mapped[int] = mapped_column(primary_key=True)

    hadith_id: Mapped[int] = mapped_column(
        ForeignKey("hadiths.id"),
        nullable=False,
    )

    scholar: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    grade: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    hadith: Mapped["Hadith"] = relationship(
        back_populates="gradings",
    )