
"""add argument evidence

Revision ID: 33f67f7b5260
Revises: bed980dc4b0e
Create Date: 2026-09-27 21:03:50.199248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "33f67f7b5260"
down_revision: Union[str, Sequence[str], None] = "bed980dc4b0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "argument_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("premise_id", sa.Integer(), nullable=True),
        sa.Column("response_id", sa.Integer(), nullable=True),
        sa.Column("result_type", sa.String(length=50), nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["premise_id"],
            ["argument_premises.id"],
        ),
        sa.ForeignKeyConstraint(
            ["response_id"],
            ["argument_responses.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.CheckConstraint(
            "(premise_id IS NOT NULL AND response_id IS NULL) "
            "OR (premise_id IS NULL AND response_id IS NOT NULL)",
            name="ck_argument_evidence_exactly_one_parent",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_argument_evidence_premise_id",
        "argument_evidence",
        ["premise_id"],
    )

    op.create_index(
        "ix_argument_evidence_response_id",
        "argument_evidence",
        ["response_id"],
    )

    op.create_index(
        "ix_argument_evidence_result",
        "argument_evidence",
        ["result_type", "result_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_argument_evidence_result",
        table_name="argument_evidence",
    )

    op.drop_index(
        "ix_argument_evidence_response_id",
        table_name="argument_evidence",
    )

    op.drop_index(
        "ix_argument_evidence_premise_id",
        table_name="argument_evidence",
    )

    op.drop_table("argument_evidence")

