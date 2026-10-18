from pydantic import BaseModel


class HadithBookResponse(BaseModel):
    id: int
    number: int
    name: str
    description: str | None