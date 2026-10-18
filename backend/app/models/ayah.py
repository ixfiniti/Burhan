from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.surah import Surah


class Ayah(Base):
    __tablename__ = "ayahs"

    id: Mapped[int] = mapped_column(primary_key=True)

    surah_id: Mapped[int] = mapped_column(
        ForeignKey("surahs.id"),
        nullable=False,
    )

    number: Mapped[int] = mapped_column(
        nullable=False,
    )

    text_arabic: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    surah: Mapped["Surah"] = relationship()