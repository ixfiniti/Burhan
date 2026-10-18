from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.argument_category import ArgumentCategory
    from app.models.argument_premise import ArgumentPremise
    from app.models.argument_objection import ArgumentObjection


class Argument(Base):
    __tablename__ = "arguments"

    id: Mapped[int] = mapped_column(primary_key=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("argument_categories.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    claim: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    conclusion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
    )

    category: Mapped["ArgumentCategory"] = relationship(
        back_populates="arguments",
    )

    premises: Mapped[list["ArgumentPremise"]] = relationship(
        back_populates="argument",
        cascade="all, delete-orphan",
        order_by="ArgumentPremise.number",
    )

    objections: Mapped[list["ArgumentObjection"]] = relationship(
        back_populates="argument",
        cascade="all, delete-orphan",
        order_by="ArgumentObjection.number",
    )