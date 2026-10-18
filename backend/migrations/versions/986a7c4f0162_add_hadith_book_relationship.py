from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "986a7c4f0162"
down_revision: Union[str, Sequence[str], None] = "6b8b28b9136c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hadiths",
        sa.Column("book_id", sa.Integer(), nullable=True),
    )

    op.execute("""
        UPDATE hadiths h
        SET book_id = b.id
        FROM hadith_chapters c
        JOIN hadith_books b ON b.id = c.book_id
        WHERE h.chapter_id = c.id
    """)

    op.execute("""
        UPDATE hadiths h
        SET book_id = b.id
        FROM hadith_books b
        WHERE h.book_id IS NULL
        AND h.reference LIKE 'Sahih al-Bukhari %'
        AND b.collection_id = (
            SELECT id
            FROM hadith_collections
            WHERE slug = 'sahih-al-bukhari'
        )
        AND split_part(h.in_book_reference, ',', 1)
            = 'Book ' || b.number
    """)

    op.alter_column(
        "hadiths",
        "book_id",
        nullable=False,
    )

    op.create_foreign_key(
        "fk_hadiths_book_id_hadith_books",
        "hadiths",
        "hadith_books",
        ["book_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_hadiths_book_id_hadith_books",
        "hadiths",
        type_="foreignkey",
    )

    op.drop_column("hadiths", "book_id")