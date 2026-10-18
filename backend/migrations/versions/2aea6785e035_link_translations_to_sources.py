"""link translations to sources

Revision ID: 2aea6785e035
Revises: 4f6344c3a540
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2aea6785e035"
down_revision: Union[str, Sequence[str], None] = "4f6344c3a540"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "translations",
        sa.Column(
            "source_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute("""
        INSERT INTO sources (
            name,
            slug,
            source_type,
            language,
            author,
            publisher,
            url,
            license,
            version,
            description,
            provenance_note
        )
        VALUES (
            'ClearQuran',
            'clearquran',
            'translation',
            'en',
            'Talal Itani',
            'ClearQuran.com',
            'https://www.clearquran.com/',
            'CC BY-ND 4.0',
            'Edition Allah',
            'English translation of the Qur''an by Talal Itani.',
            'Translation files were obtained from the official ClearQuran distribution. The ClearQuran distribution permits sharing and redistribution when the translation remains unmodified and attribution is preserved.'
        )
        ON CONFLICT (slug) DO NOTHING
    """)

    op.execute("""
        UPDATE translations
        SET source_id = (
            SELECT id
            FROM sources
            WHERE slug = 'clearquran'
        )
        WHERE language = 'en'
          AND translator = 'Talal Itani'
    """)

    op.alter_column(
        "translations",
        "source_id",
        nullable=False,
    )

    op.create_foreign_key(
        "fk_translations_source_id_sources",
        "translations",
        "sources",
        ["source_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_translations_source_id_sources",
        "translations",
        type_="foreignkey",
    )

    op.drop_column(
        "translations",
        "source_id",
    )

    op.execute("""
        DELETE FROM sources
        WHERE slug = 'clearquran'
    """)