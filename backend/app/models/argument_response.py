
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.argument_objection import ArgumentObjection
    from app.models.argument_evidence import ArgumentEvidence


class ArgumentResponse(Base):
    __tablename__ = "argument_responses"

    id: Mapped[int] = mapped_column(primary_key=True)

    objection_id: Mapped[int] = mapped_column(
        ForeignKey("argument_objections.id"),
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

    objection: Mapped["ArgumentObjection"] = relationship(
        back_populates="responses",
    )

    evidence: Mapped[list["ArgumentEvidence"]] = relationship(
        back_populates="response",
        cascade="all, delete-orphan",
    )

