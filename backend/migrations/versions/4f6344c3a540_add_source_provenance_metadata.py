"""add source provenance metadata

Revision ID: 4f6344c3a540
Revises: a0a4d1c0cada
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f6344c3a540"
down_revision: Union[str, Sequence[str], None] = "a0a4d1c0cada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column(
            "url",
            sa.String(length=1000),
            nullable=True,
        ),
    )

    op.add_column(
        "sources",
        sa.Column(
            "license",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "sources",
        sa.Column(
            "version",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "sources",
        sa.Column(
            "provenance_note",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("sources", "provenance_note")
    op.drop_column("sources", "version")
    op.drop_column("sources", "license")
    op.drop_column("sources", "url")