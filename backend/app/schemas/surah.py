from pydantic import BaseModel


class SurahResponse(BaseModel):
    id: int
    number: int
    name_arabic: str
    name_transliteration: str
    name_english: str