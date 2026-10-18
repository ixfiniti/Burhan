from pydantic import BaseModel


class AIAnswerEvidence(BaseModel):
    evidence_number: int
    reference: str
    result_type: str


class AIAnswerClaim(BaseModel):
    claim: str
    support_level: str
    evidence_numbers: list[int]
    grounded: bool
    grounding_reason: str


class AIAnswerGroundingIssue(BaseModel):
    sentence: str
    reason: str


class AIAnswerResponse(BaseModel):
    question: str
    answer: str
    answer_grounded: bool
    answer_grounding_issues: list[AIAnswerGroundingIssue]
    claims: list[AIAnswerClaim]
    evidence: list[AIAnswerEvidence]