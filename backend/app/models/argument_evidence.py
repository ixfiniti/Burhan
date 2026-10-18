from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.argument_premise import ArgumentPremise
    from app.models.argument_response import ArgumentResponse


class ArgumentEvidence(Base):
    __tablename__ = "argument_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)

    premise_id: Mapped[int | None] = mapped_column(
        ForeignKey("argument_premises.id"),
        nullable=True,
    )

    response_id: Mapped[int | None] = mapped_column(
        ForeignKey("argument_responses.id"),
        nullable=True,
    )

    result_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    result_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id"),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="supporting",
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    premise: Mapped["ArgumentPremise | None"] = relationship(
        back_populates="evidence",
    )

    response: Mapped["ArgumentResponse | None"] = relationship(
        back_populates="evidence",
    )