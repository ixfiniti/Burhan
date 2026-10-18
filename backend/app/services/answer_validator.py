import json

from pydantic import BaseModel

from app.schemas.ai_context import AIContextResponse
from app.services.ollama import generate_answer


ANSWER_GROUNDING_SYSTEM_PROMPT = """
You are the final answer-grounding validator for Burhān.

Your job is to check EVERY factual sentence in an AI-generated answer
against the supplied Burhān evidence.

Rules:

1. Evaluate each sentence independently.

2. A sentence is grounded only if the supplied evidence directly supports
   the factual content of that sentence.

3. Do not use outside knowledge.

4. Be extremely strict about overclaiming.

5. Do not treat implications, themes, significance, importance,
   theological conclusions, historical conclusions, social conclusions,
   ritual conclusions, or broader lessons as directly supported unless the
   supplied evidence explicitly states or clearly establishes them.

6. If a sentence adds a broader interpretation to an otherwise supported
   fact, mark the sentence as NOT grounded.

7. A hadith describing an event does not automatically establish a broader
   theological, historical, social, or ritual conclusion.

8. If a sentence contains both supported and unsupported factual content,
   mark the sentence as NOT grounded.

9. If the evidence supports only part of a sentence, mark the entire
   sentence as NOT grounded.

10. Pay close attention to the actual Arabic and English evidence.

11. Do not infer that something is an "important", "central", "essential",
    "fundamental", "significant", or "core" teaching merely because the
    evidence mentions it.

12. Do not infer general Islamic teachings from a single event unless the
    supplied evidence itself explicitly makes that generalization.

13. Do not infer the significance, purpose, wisdom, or theological meaning
    of an action unless the supplied evidence explicitly establishes it.

14. Distinguish between what the source explicitly says and what a reader
    might reasonably interpret from it. Reasonable interpretation is still
    considered NOT grounded for this final answer validator unless the
    evidence clearly establishes the interpretation.

15. A factual sentence should be considered grounded only when a careful
    reader could verify the sentence directly from the supplied evidence
    without needing outside knowledge or additional reasoning.

16. Ignore purely stylistic sentences that contain no factual claim.

Return ONLY valid JSON:

{
  "grounded": true,
  "issues": [
    {
      "sentence": "The unsupported sentence.",
      "reason": "Why the supplied evidence does not directly support it."
    }
  ]
}

If every factual sentence is directly supported:

{
  "grounded": true,
  "issues": []
}

If one or more sentences are unsupported or overextended:

{
  "grounded": false,
  "issues": [
    {
      "sentence": "The unsupported sentence.",
      "reason": "Brief explanation."
    }
  ]
}

Do not use Markdown.
Do not include anything outside the JSON object.
"""


class AnswerGroundingIssue(BaseModel):
    sentence: str
    reason: str


class AnswerGroundingResult(BaseModel):
    grounded: bool
    issues: list[AnswerGroundingIssue]


def validate_answer(
    answer: str,
    context: AIContextResponse,
) -> AnswerGroundingResult:

    evidence_sections = []

    for item in context.evidence:
        evidence_sections.append(
            f"""
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
        )

    evidence_text = "\n".join(evidence_sections)

    user_prompt = f"""
AI-generated answer:

{answer}

Supplied Burhān evidence:

{evidence_text}

Check every factual sentence in the AI-generated answer against the
supplied evidence.

Identify EVERY sentence whose factual content is unsupported,
overextended, generalized, or interpretive beyond what the evidence
directly establishes.

Be conservative.

If a sentence says something broader than the evidence itself says,
mark it as NOT grounded.

Return ONLY the required JSON object.
"""

    raw_result = generate_answer(
        system_prompt=ANSWER_GROUNDING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    try:
        data = json.loads(raw_result)
    except json.JSONDecodeError:
        raise ValueError(
            "Answer grounding validator returned invalid JSON"
        )

    return AnswerGroundingResult(
        grounded=bool(data["grounded"]),
        issues=[
            AnswerGroundingIssue(
                sentence=issue["sentence"],
                reason=issue["reason"],
            )
            for issue in data.get("issues", [])
        ],
    )