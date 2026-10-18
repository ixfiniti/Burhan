from pydantic import BaseModel


class ClaimValidation(BaseModel):
    claim: str
    support_level: str
    evidence_numbers: list[int]
    grounded: bool
    reason: str