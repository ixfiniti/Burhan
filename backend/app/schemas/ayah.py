from pydantic import BaseModel

from app.schemas.surah import SurahResponse
from app.schemas.translation import TranslationResponse


class AyahResponse(BaseModel):
    id: int
    number: int
    text_arabic: str


class AyahNavigationResponse(BaseModel):
    id: int
    number: int
    reference: str


class AyahWithTranslationsResponse(BaseModel):
    surah: SurahResponse
    ayah: AyahResponse
    translations: list[TranslationResponse]
    previous: AyahNavigationResponse | None = None
    next: AyahNavigationResponse | None = None


class SurahAyahResponse(BaseModel):
    number: int
    text_arabic: str
    translations: list[TranslationResponse]


class SurahWithAyahsResponse(BaseModel):
    surah: SurahResponse
    ayahs: list[SurahAyahResponse]