from app.schemas.ai_answer import AIAnswerResponse


VALID_SUPPORT_LEVELS = {
    "explicit",
    "interpretation",
    "insufficient",
}


def validate_ai_answer(
    answer: AIAnswerResponse,
) -> AIAnswerResponse:
    valid_evidence_numbers = {
        item.evidence_number
        for item in answer.evidence
    }

    for claim in answer.claims:
        if claim.support_level not in VALID_SUPPORT_LEVELS:
            raise ValueError(
                f"Invalid support level: {claim.support_level}"
            )

        if not claim.evidence_numbers:
            raise ValueError(
                f"Claim has no evidence: {claim.claim}"
            )

        for evidence_number in claim.evidence_numbers:
            if evidence_number not in valid_evidence_numbers:
                raise ValueError(
                    f"Claim references nonexistent evidence: "
                    f"{evidence_number}"
                )

    return answer