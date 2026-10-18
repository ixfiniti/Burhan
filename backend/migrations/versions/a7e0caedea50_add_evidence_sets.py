"""add evidence sets

Revision ID: a7e0caedea50
Revises: 2aea6785e035
Create Date: 2026-09-21 00:09:59.633409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7e0caedea50"
down_revision: Union[str, Sequence[str], None] = "2aea6785e035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "evidence_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evidence_set_id", sa.Integer(), nullable=False),
        sa.Column("result_type", sa.String(length=20), nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_set_id"],
            ["evidence_sets.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("evidence_items")
    op.drop_table("evidence_sets")