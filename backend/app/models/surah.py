from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Surah(Base):
    __tablename__ = "surahs"

    id: Mapped[int] = mapped_column(primary_key=True)

    number: Mapped[int] = mapped_column(
        unique=True,
        nullable=False,
    )

    name_arabic: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name_transliteration: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name_english: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )