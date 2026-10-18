
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.argument import Argument
    from app.models.argument_evidence import ArgumentEvidence


class ArgumentPremise(Base):
    __tablename__ = "argument_premises"

    id: Mapped[int] = mapped_column(primary_key=True)

    argument_id: Mapped[int] = mapped_column(
        ForeignKey("arguments.id"),
        nullable=False,
    )

    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    argument: Mapped["Argument"] = relationship(
        back_populates="premises",
    )

    evidence: Mapped[list["ArgumentEvidence"]] = relationship(
        back_populates="premise",
        cascade="all, delete-orphan",
    )

