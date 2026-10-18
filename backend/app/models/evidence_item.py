
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.evidence_set import EvidenceSet
    from app.models.source import Source


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    evidence_set_id: Mapped[int] = mapped_column(
        ForeignKey("evidence_sets.id"),
        nullable=False,
    )

    result_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    result_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    evidence_set: Mapped["EvidenceSet"] = relationship(
        back_populates="items",
    )

    source: Mapped["Source"] = relationship()

