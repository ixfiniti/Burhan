from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.surah import Surah
from app.models.ayah import Ayah


QURAN_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "quran"
    / "quran-simple-min.txt"
)


SURAH_NAMES = [
    ("الفاتحة", "Al-Fatihah", "The Opening"),
    ("البقرة", "Al-Baqarah", "The Cow"),
    ("آل عمران", "Aal-Imran", "The Family of Imran"),
    ("النساء", "An-Nisa", "The Women"),
    ("المائدة", "Al-Ma'idah", "The Table Spread"),
    ("الأنعام", "Al-An'am", "The Cattle"),
    ("الأعراف", "Al-A'raf", "The Heights"),
    ("الأنفال", "Al-Anfal", "The Spoils of War"),
    ("التوبة", "At-Tawbah", "The Repentance"),
    ("يونس", "Yunus", "Jonah"),
    ("هود", "Hud", "Hud"),
    ("يوسف", "Yusuf", "Joseph"),
    ("الرعد", "Ar-Ra'd", "The Thunder"),
    ("إبراهيم", "Ibrahim", "Abraham"),
    ("الحجر", "Al-Hijr", "The Rocky Tract"),
    ("النحل", "An-Nahl", "The Bee"),
    ("الإسراء", "Al-Isra", "The Night Journey"),
    ("الكهف", "Al-Kahf", "The Cave"),
    ("مريم", "Maryam", "Mary"),
    ("طه", "Ta-Ha", "Ta-Ha"),
    ("الأنبياء", "Al-Anbiya", "The Prophets"),
    ("الحج", "Al-Hajj", "The Pilgrimage"),
    ("المؤمنون", "Al-Mu'minun", "The Believers"),
    ("النور", "An-Nur", "The Light"),
    ("الفرقان", "Al-Furqan", "The Criterion"),
    ("الشعراء", "Ash-Shu'ara", "The Poets"),
    ("النمل", "An-Naml", "The Ant"),
    ("القصص", "Al-Qasas", "The Stories"),
    ("العنكبوت", "Al-Ankabut", "The Spider"),
    ("الروم", "Ar-Rum", "The Romans"),
    ("لقمان", "Luqman", "Luqman"),
    ("السجدة", "As-Sajdah", "The Prostration"),
    ("الأحزاب", "Al-Ahzab", "The Combined Forces"),
    ("سبأ", "Saba", "Sheba"),
    ("فاطر", "Fatir", "The Originator"),
    ("يس", "Ya-Sin", "Ya-Sin"),
    ("الصافات", "As-Saffat", "Those Ranges in Ranks"),
    ("ص", "Sad", "Sad"),
    ("الزمر", "Az-Zumar", "The Groups"),
    ("غافر", "Ghafir", "The Forgiver"),
    ("فصلت", "Fussilat", "Explained in Detail"),
    ("الشورى", "Ash-Shura", "The Consultation"),
    ("الزخرف", "Az-Zukhruf", "The Ornaments of Gold"),
    ("الدخان", "Ad-Dukhan", "The Smoke"),
    ("الجاثية", "Al-Jathiyah", "The Crouching"),
    ("الأحقاف", "Al-Ahqaf", "The Wind-Curved Sandhills"),
    ("محمد", "Muhammad", "Muhammad"),
    ("الفتح", "Al-Fath", "The Victory"),
    ("الحجرات", "Al-Hujurat", "The Rooms"),
    ("ق", "Qaf", "Qaf"),
    ("الذاريات", "Adh-Dhariyat", "The Winnowing Winds"),
    ("الطور", "At-Tur", "The Mount"),
    ("النجم", "An-Najm", "The Star"),
    ("القمر", "Al-Qamar", "The Moon"),
    ("الرحمن", "Ar-Rahman", "The Beneficent"),
    ("الواقعة", "Al-Waqi'ah", "The Inevitable"),
    ("الحديد", "Al-Hadid", "The Iron"),
    ("المجادلة", "Al-Mujadilah", "The Pleading Woman"),
    ("الحشر", "Al-Hashr", "The Exile"),
    ("الممتحنة", "Al-Mumtahanah", "The Woman to be Examined"),
    ("الصف", "As-Saff", "The Ranks"),
    ("الجمعة", "Al-Jumu'ah", "Friday"),
    ("المنافقون", "Al-Munafiqun", "The Hypocrites"),
    ("التغابن", "At-Taghabun", "Mutual Disillusion"),
    ("الطلاق", "At-Talaq", "The Divorce"),
    ("التحريم", "At-Tahrim", "The Prohibition"),
    ("الملك", "Al-Mulk", "The Sovereignty"),
    ("القلم", "Al-Qalam", "The Pen"),
    ("الحاقة", "Al-Haqqah", "The Reality"),
    ("المعارج", "Al-Ma'arij", "The Ascending Stairways"),
    ("نوح", "Nuh", "Noah"),
    ("الجن", "Al-Jinn", "The Jinn"),
    ("المزمل", "Al-Muzzammil", "The Enshrouded One"),
    ("المدثر", "Al-Muddaththir", "The Cloaked One"),
    ("القيامة", "Al-Qiyamah", "The Resurrection"),
    ("الإنسان", "Al-Insan", "Man"),
    ("المرسلات", "Al-Mursalat", "Those Sent Forth"),
    ("النبأ", "An-Naba", "The Tidings"),
    ("النازعات", "An-Nazi'at", "Those Who Drag Forth"),
    ("عبس", "Abasa", "He Frowned"),
    ("التكوير", "At-Takwir", "The Overthrowing"),
    ("الانفطار", "Al-Infitar", "The Cleaving"),
    ("المطففين", "Al-Mutaffifin", "The Defrauding"),
    ("الانشقاق", "Al-Inshiqaq", "The Splitting Asunder"),
    ("البروج", "Al-Buruj", "The Mansions of the Stars"),
    ("الطارق", "At-Tariq", "The Nightcomer"),
    ("الأعلى", "Al-A'la", "The Most High"),
    ("الغاشية", "Al-Ghashiyah", "The Overwhelming"),
    ("الفجر", "Al-Fajr", "The Dawn"),
    ("البلد", "Al-Balad", "The City"),
    ("الشمس", "Ash-Shams", "The Sun"),
    ("الليل", "Al-Layl", "The Night"),
    ("الضحى", "Ad-Duha", "The Morning Brightness"),
    ("الشرح", "Ash-Sharh", "The Relief"),
    ("التين", "At-Tin", "The Fig"),
    ("العلق", "Al-Alaq", "The Clot"),
    ("القدر", "Al-Qadr", "The Power"),
    ("البينة", "Al-Bayyinah", "The Clear Proof"),
    ("الزلزلة", "Az-Zalzalah", "The Earthquake"),
    ("العاديات", "Al-Adiyat", "The Courser"),
    ("القارعة", "Al-Qari'ah", "The Striking Calamity"),
    ("التكاثر", "At-Takathur", "The Rivalry in World Increase"),
    ("العصر", "Al-Asr", "Time"),
    ("الهمزة", "Al-Humazah", "The Slanderer"),
    ("الفيل", "Al-Fil", "The Elephant"),
    ("قريش", "Quraysh", "Quraysh"),
    ("الماعون", "Al-Ma'un", "The Small Kindnesses"),
    ("الكوثر", "Al-Kawthar", "The Abundance"),
    ("الكافرون", "Al-Kafirun", "The Disbelievers"),
    ("النصر", "An-Nasr", "The Divine Support"),
    ("المسد", "Al-Masad", "The Palm Fiber"),
    ("الإخلاص", "Al-Ikhlas", "Sincerity"),
    ("الفلق", "Al-Falaq", "The Daybreak"),
    ("الناس", "An-Nas", "Mankind"),
]


def import_quran():
    if not QURAN_FILE.exists():
        raise FileNotFoundError(f"Qur'an file not found: {QURAN_FILE}")

    db = SessionLocal()

    try:
        print("Clearing existing Qur'an ayahs and surahs...")

        db.query(Ayah).delete()
        db.query(Surah).delete()
        db.commit()

        print("Importing 114 surahs...")

        for number, (arabic, transliteration, english) in enumerate(
            SURAH_NAMES,
            start=1,
        ):
            db.add(
                Surah(
                    number=number,
                    name_arabic=arabic,
                    name_transliteration=transliteration,
                    name_english=english,
                )
            )

        db.commit()

        surahs = {
            surah.number: surah
            for surah in db.query(Surah).all()
        }

        print("Importing ayahs...")

        ayah_count = 0

        with QURAN_FILE.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.rstrip("\n\r")

                if not line:
                 continue

                if line.startswith("#"):
                    continue

                parts = line.split("|", 2)

                if len(parts) != 3:
                    raise ValueError(
                        f"Invalid format on line {line_number}: {line}"
                    )

                surah_number = int(parts[0])
                ayah_number = int(parts[1])
                text_arabic = parts[2]

                surah = surahs.get(surah_number)

                if surah is None:
                    raise ValueError(
                        f"Unknown surah number {surah_number} "
                        f"on line {line_number}"
                    )

                db.add(
                    Ayah(
                        surah_id=surah.id,
                        number=ayah_number,
                        text_arabic=text_arabic,
                    )
                )

                ayah_count += 1

        db.commit()

        print(f"Imported {len(surahs)} surahs.")
        print(f"Imported {ayah_count} ayahs.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_quran()