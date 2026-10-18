"""link hadith collections to sources

Revision ID: a0a4d1c0cada
Revises: 2330fa2a2a0b
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a0a4d1c0cada"
down_revision: Union[str, Sequence[str], None] = "2330fa2a2a0b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the column as nullable first because existing collections exist.
    op.add_column(
        "hadith_collections",
        sa.Column(
            "source_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Create the Bukhari source record.
    op.execute("""
        INSERT INTO sources (
            name,
            slug,
            source_type,
            language,
            author,
            publisher,
            description
        )
        VALUES (
            'Sahih al-Bukhari',
            'sahih-al-bukhari',
            'hadith',
            'ar',
            'Imam Bukhari',
            'Sunnah.com',
            'Sahih al-Bukhari hadith collection. Structured source data imported from the open-hadith-data project.'
        )
        ON CONFLICT (slug) DO NOTHING
    """)

    # Link the existing Bukhari collection to the source.
    op.execute("""
        UPDATE hadith_collections
        SET source_id = (
            SELECT id
            FROM sources
            WHERE slug = 'sahih-al-bukhari'
        )
        WHERE slug = 'sahih-al-bukhari'
    """)

    # Make the relationship mandatory now that existing data is populated.
    op.alter_column(
        "hadith_collections",
        "source_id",
        nullable=False,
    )

    # Add the foreign-key constraint.
    op.create_foreign_key(
        "fk_hadith_collections_source_id_sources",
        "hadith_collections",
        "sources",
        ["source_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_hadith_collections_source_id_sources",
        "hadith_collections",
        type_="foreignkey",
    )

    op.drop_column(
        "hadith_collections",
        "source_id",
    )

    op.execute("""
        DELETE FROM sources
        WHERE slug = 'sahih-al-bukhari'
    """)