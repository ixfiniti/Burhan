from pydantic import BaseModel


class HadithChapterResponse(BaseModel):
    id: int
    number: int
    name: str | None
    description: str | None