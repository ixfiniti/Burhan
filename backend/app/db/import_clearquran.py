from pathlib import Path
import re

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ayah import Ayah
from app.models.surah import Surah
from app.models.translation import Translation


CLEARQURAN_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "quran"
    / "clearquran"
)

TRANSLATOR = "Talal Itani"
LANGUAGE = "en"

FILENAME_PATTERN = re.compile(r"^(\d{3})-(\d{3})\.txt$")


def import_clearquran():
    if not CLEARQURAN_DIR.exists():
        raise FileNotFoundError(
            f"ClearQuran directory not found: {CLEARQURAN_DIR}"
        )

    db = SessionLocal()

    try:
        surahs = {
            surah.number: surah
            for surah in db.query(Surah).all()
        }

        ayahs = {
            (ayah.surah_id, ayah.number): ayah
            for ayah in db.query(Ayah).all()
        }

        print(f"Found {len(surahs)} surahs.")
        print(f"Found {len(ayahs)} Qur'an ayahs in database.")

        imported = 0
        skipped = 0

        files = sorted(CLEARQURAN_DIR.glob("*.txt"))

        for file_path in files:
            match = FILENAME_PATTERN.match(file_path.name)

            if match is None:
                skipped += 1
                continue

            surah_number = int(match.group(1))
            ayah_number = int(match.group(2))

            # 000 files contain surah-level material, not ayahs.
            if ayah_number == 0:
                skipped += 1
                continue

            surah = surahs.get(surah_number)

            if surah is None:
                raise ValueError(
                    f"No matching surah for {file_path.name}"
                )

            ayah = ayahs.get((surah.id, ayah_number))

            if ayah is None:
                raise ValueError(
                    f"No matching Qur'an ayah for {file_path.name}"
                )

            text = file_path.read_text(
                encoding="utf-8"
            ).rstrip("\r\n")

            existing = db.scalar(
                select(Translation).where(
                    Translation.ayah_id == ayah.id,
                    Translation.language == LANGUAGE,
                    Translation.translator == TRANSLATOR,
                )
            )

            if existing:
                existing.text = text
            else:
                db.add(
                    Translation(
                        ayah_id=ayah.id,
                        language=LANGUAGE,
                        translator=TRANSLATOR,
                        text=text,
                    )
                )

            imported += 1

        db.commit()

        print(f"Imported/updated: {imported} translations.")
        print(f"Skipped: {skipped} files.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_clearquran()