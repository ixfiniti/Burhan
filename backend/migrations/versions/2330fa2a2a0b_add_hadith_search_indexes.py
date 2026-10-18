"""add hadith search indexes

Revision ID: 2330fa2a2a0b
Revises: 986a7c4f0162
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op


revision: str = "2330fa2a2a0b"
down_revision: Union[str, Sequence[str], None] = "986a7c4f0162"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX ix_hadiths_arabic_search
        ON hadiths
        USING GIN (
            to_tsvector(
                'simple',
                text_arabic
            )
        )
    """)

    op.execute("""
        CREATE INDEX ix_hadith_translations_english_search
        ON hadith_translations
        USING GIN (
            to_tsvector(
                'english',
                text
            )
        )
        WHERE language = 'en'
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS ix_hadith_translations_english_search
    """)

    op.execute("""
        DROP INDEX IF EXISTS ix_hadiths_arabic_search
    """)