from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.argument import Argument
    from app.models.argument_response import ArgumentResponse


class ArgumentObjection(Base):
    __tablename__ = "argument_objections"

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
        back_populates="objections",
    )

    responses: Mapped[list["ArgumentResponse"]] = relationship(
        back_populates="objection",
        cascade="all, delete-orphan",
        order_by="ArgumentResponse.number",
    )