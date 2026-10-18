import sqlite3

SQLITE_PATH = r"data\hadith\hadiths.db"

db = sqlite3.connect(SQLITE_PATH)
db.row_factory = sqlite3.Row

rows = db.execute("""
    SELECT
        hadith_number,
        reference,
        text_en,
        url_source
    FROM hadiths
    WHERE collection_id = 'bukhari'
    ORDER BY id
    LIMIT 3
""").fetchall()

for row in rows:
    print("=" * 80)
    print("NUMBER:", row["hadith_number"])
    print("REFERENCE:", row["reference"])
    print("URL SOURCE:", repr(row["url_source"]))
    print("TEXT EN:", repr(row["text_en"]))

db.close()