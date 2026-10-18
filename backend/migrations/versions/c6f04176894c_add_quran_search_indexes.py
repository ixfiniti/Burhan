"""add quran search indexes

Revision ID: c6f04176894c
Revises: 0c708053a24c
Create Date: 2026-09-20 10:21:27.891957
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c6f04176894c"
down_revision: Union[str, Sequence[str], None] = "0c708053a24c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX ix_translations_english_search
        ON translations
        USING GIN (
            to_tsvector(
                'english',
                text
            )
        )
        WHERE language = 'en'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_translations_english_search
        """
    )