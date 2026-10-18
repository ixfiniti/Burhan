import json

from app.schemas.ai_answer import AIAnswerClaim
from app.schemas.ai_context import AIContextResponse
from app.services.ollama import generate_answer
from app.schemas.claim_validation import ClaimValidation


GROUNDING_SYSTEM_PROMPT = """
You are the evidence-grounding validator for Burhān.

Your job is NOT to answer the user's question.

Your only job is to determine whether an AI-generated claim is actually
supported by the supplied evidence.

Rules:

1. A claim is grounded only if the cited evidence actually supports it.

2. "explicit" means the evidence directly states or clearly establishes
   the claim.

3. "interpretation" means the claim is a reasonable interpretation of the
   evidence, but is not directly stated.

4. "insufficient" means the evidence does not adequately support the claim.

5. Do not add outside knowledge.

6. Do not assume that a hadith says something merely because it concerns
   a similar topic.

7. Pay close attention to the actual Arabic and English text.

8. If the claim overstates what the evidence says, mark it as not grounded.

Return ONLY valid JSON:

{
  "grounded": true,
  "reason": "Brief explanation."
}

Do not use Markdown.
Do not include any text outside the JSON object.
"""


def validate_claim(
    claim: AIAnswerClaim,
    context: AIContextResponse,
) -> ClaimValidation:

    selected_evidence = [
        item
        for item in context.evidence
        if item.evidence_number in claim.evidence_numbers
    ]

    evidence_text = ""

    for item in selected_evidence:
        evidence_text += f"""
[Evidence {item.evidence_number}]
Type: {item.result_type}
Reference: {item.reference}

Arabic:
{item.text_arabic}

English translation:
{item.translation}

Source:
{item.source_name}

Provenance:
{item.source_provenance}

"""

    user_prompt = f"""
Claim:

{claim.claim}

Claim support level:

{claim.support_level}

Cited evidence:

{evidence_text}

Determine whether this claim is actually supported by the cited evidence.

Return ONLY the required JSON object.
"""

    raw_result = generate_answer(
        system_prompt=GROUNDING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    try:
        data = json.loads(raw_result)
    except json.JSONDecodeError:
        raise ValueError("Grounding validator returned invalid JSON")

    return ClaimValidation(
        claim=claim.claim,
        support_level=claim.support_level,
        evidence_numbers=claim.evidence_numbers,
        grounded=bool(data["grounded"]),
        reason=data["reason"],
    )