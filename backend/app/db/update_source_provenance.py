from app.db.session import SessionLocal
from app.models.source import Source


def update_sources() -> None:
    db = SessionLocal()

    try:
        quran = (
            db.query(Source)
            .filter(Source.slug == "quran")
            .first()
        )

        if quran:
            quran.url = "https://tanzil.net/"
            quran.license = "Tanzil Quran text; verify current redistribution terms at source"
            quran.version = "Tanzil Simple Minimal"
            quran.provenance_note = (
                "Arabic Qur'an text imported from the Tanzil Quran text "
                "download configured as Simple (Minimal), with pause marks, "
                "sajdah signs, rub-el-hizb marks, and tatweel disabled."
            )

        bukhari = (
            db.query(Source)
            .filter(Source.slug == "sahih-al-bukhari")
            .first()
        )

        if bukhari:
            bukhari.url = "https://sunnah.com/bukhari"
            bukhari.license = (
                "Structured data: CC0 1.0 Public Domain. "
                "English translation provenance requires verification of "
                "Sunnah.com redistribution terms."
            )
            bukhari.version = "open-hadith-data v1.0.0"
            bukhari.provenance_note = (
                "Original textual source: Sunnah.com / Sahih al-Bukhari. "
                "Structured data was obtained from Jaguar16/open-hadith-data "
                "v1.0.0 and imported into Burhan. The dataset is an automated "
                "extraction and should be checked against authenticated "
                "printed editions and qualified scholarship for scholarly use."
            )

        db.commit()

        print("Source provenance updated.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    update_sources()