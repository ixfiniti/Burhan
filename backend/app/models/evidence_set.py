from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.evidence_item import EvidenceItem


class EvidenceSet(Base):
    __tablename__ = "evidence_sets"

    id: Mapped[int] = mapped_column(primary_key=True)

    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    items: Mapped[list["EvidenceItem"]] = relationship(
        back_populates="evidence_set",
        cascade="all, delete-orphan",
    )