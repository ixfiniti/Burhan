"""expand source metadata

Revision ID: 2eba223b7ba5
Revises: 13e77ee34878
Create Date: 2026-09-19 17:57:59.134516
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2eba223b7ba5"
down_revision: Union[str, Sequence[str], None] = "13e77ee34878"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "sources",
        sa.Column("slug", sa.String(length=255), nullable=False),
    )

    op.add_column(
        "sources",
        sa.Column("language", sa.String(length=20), nullable=False),
    )

    op.add_column(
        "sources",
        sa.Column("author", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "sources",
        sa.Column("publisher", sa.String(length=255), nullable=True),
    )

    op.create_unique_constraint(
        "uq_sources_slug",
        "sources",
        ["slug"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_sources_slug",
        "sources",
        type_="unique",
    )

    op.drop_column("sources", "publisher")
    op.drop_column("sources", "author")
    op.drop_column("sources", "language")
    op.drop_column("sources", "slug")