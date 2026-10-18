from sqlalchemy import text
from app.db.session import SessionLocal

db = SessionLocal()

result = db.execute(
    text("""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT id
        FROM translations
        WHERE language = 'en'
        AND to_tsvector('english', text)
            @@ plainto_tsquery('english', 'mercy forgiveness')
    """)
)

for row in result:
    print(row[0])

db.close()
