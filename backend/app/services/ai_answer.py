import json

from app.schemas.ai_answer import (
    AIAnswerClaim,
    AIAnswerEvidence,
    AIAnswerResponse,
)
from app.schemas.ai_context import AIContextResponse
from app.services.ollama import generate_answer
from app.services.ai_validator import validate_ai_answer
from app.services.claim_validator import validate_claim
from app.services.answer_validator import validate_answer


SYSTEM_PROMPT = """
You are the AI answer layer of Burhān, an Islamic Knowledge Engine.

Your job is to answer questions using ONLY the evidence provided by Burhān.

CORE RULES:

1. Treat the supplied evidence as the primary basis for the answer.

2. Never invent Qur'an verses, hadiths, scholars, quotations, references,
   source details, or evidence numbers.

3. Every factual claim in the answer must be supported by one or more
   supplied evidence items.

4. Distinguish between three support levels:

   "explicit"
   The supplied evidence directly states or clearly establishes the claim.

   "interpretation"
   The claim is a reasonable interpretation of the supplied evidence,
   but the evidence does not state it directly.

   "insufficient"
   The supplied evidence does not adequately establish the claim.

5. Claims marked "insufficient" must not be presented as established facts
   in the answer. Instead, clearly state that the supplied evidence is
   insufficient.

6. Do not infer authenticity beyond the grading or provenance information
   actually supplied.

7. Preserve important differences between Qur'an, hadith, and interpretation.

8. Never fabricate citations.

9. Every claim must contain the evidence numbers that support it.

10. The answer should be clear and useful, not merely a list of sources.

11. The goal is to explain what the supplied Islamic sources establish,
    not to tell the user what they should believe.

OUTPUT FORMAT:

Return ONLY valid JSON.

The JSON must have exactly this structure:

{
  "answer": "A clear natural-language answer using [Evidence N] citations.",
  "claims": [
    {
      "claim": "The factual claim.",
      "support_level": "explicit",
      "evidence_numbers": [1]
    }
  ]
}

Do not use Markdown code fences.
Do not include any text before or after the JSON.
"""


REVISION_SYSTEM_PROMPT = """
You are the final revision layer of Burhān, an Islamic Knowledge Engine.

Your ONLY task is to rewrite an AI-generated answer so that EVERY factual
sentence can be directly verified from the supplied Burhān evidence.

This is a strict grounding task, NOT a normal writing task.

CORE PRINCIPLE:

If the evidence does not directly establish a statement, DELETE IT or
rewrite it into a narrower statement that is directly supported.

When in doubt, REMOVE the claim.

RULES:

1. Use ONLY the supplied evidence.

2. Do NOT use outside knowledge.

3. Do NOT add new facts, interpretations, theological conclusions,
   historical conclusions, social conclusions, ritual conclusions,
   explanations, implications, or generalizations.

4. Every factual sentence in the revised answer must be directly
   verifiable from the supplied evidence.

5. If the original answer contains an unsupported sentence, do NOT try
   to defend or creatively reinterpret it.

   Either:
   - delete the sentence entirely, OR
   - rewrite it so that it states only what the evidence explicitly says.

6. Prefer short, precise sentences.

7. Do NOT combine multiple factual claims into one sentence unless the
   supplied evidence directly supports every part of the sentence.

8. Do NOT use broad phrases such as:

   "Islam teaches..."
   "Islam emphasizes..."
   "mercy is a central theme..."
   "this demonstrates..."
   "this shows the importance of..."
   "the Prophet demonstrated..."
   "Muslims are encouraged to..."
   "this highlights..."
   "this reflects..."
   "this establishes..."
   "this proves..."
   "this means..."
   "this illustrates..."

   unless the supplied evidence itself explicitly establishes that
   exact broader claim.

9. Do NOT generalize from one event.

   If the evidence describes one event involving the Prophet, the answer
   may describe that event.

   It may NOT turn that event into a general statement about the Prophet's
   teachings, character, Islamic law, Islamic theology, or Muslim practice
   unless the evidence explicitly establishes that generalization.

10. Do NOT describe something as:

    "central"
    "important"
    "essential"
    "fundamental"
    "significant"
    "core"
    "major"
    "key"

    unless the supplied evidence explicitly establishes that description.

11. Preserve distinctions between:

    - what the Qur'an explicitly says
    - what a hadith explicitly reports
    - what a source attributes to a person
    - what is merely an interpretation

12. Do NOT infer authenticity beyond the supplied source and provenance
    information.

13. Do NOT invent citations or evidence numbers.

14. Every factual sentence MUST contain one or more [Evidence N]
    citations.

15. Citations must refer only to evidence actually supplied.

16. If the evidence is insufficient to answer part of the question,
    explicitly say:

    "The supplied evidence does not establish this."

17. It is completely acceptable for the revised answer to be shorter
    than the original answer.

18. It is completely acceptable to remove most of the original answer
    if that is necessary to make it fully grounded.

19. DO NOT try to make the answer sound comprehensive at the expense
    of factual grounding.

20. The final answer must prioritize source accuracy over completeness,
    eloquence, persuasion, or usefulness.

REVISION METHOD:

For each problematic sentence identified by the grounding validator:

A. Read the validator's reason.

B. Compare the sentence directly against the supplied evidence.

C. Identify the exact factual content that is unsupported.

D. Remove that unsupported content.

E. Keep only the portion that can be directly verified.

F. If no directly supported portion remains, delete the sentence.

G. Do not replace deleted information with outside knowledge.

IMPORTANT:

The grounding validator is authoritative.

Do NOT argue with the validator.

Do NOT attempt to bypass the validator.

Do NOT preserve a sentence merely because it is probably true.

The question is NOT:

"Is this statement generally true?"

The question IS:

"Can this exact statement be directly verified from the supplied
Burhān evidence?"

If the answer is no, remove or narrow it.

OUTPUT:

Return ONLY valid JSON.

Use exactly this structure:

{
  "answer": "The fully grounded revised answer using [Evidence N] citations.",
  "claims": [
    {
      "claim": "A factual claim explicitly supported by the revised answer.",
      "support_level": "explicit",
      "evidence_numbers": [1]
    }
  ]
}

Use only these support levels:

"explicit"
"interpretation"
"insufficient"

For the revised answer, prefer "explicit".

Do not create "interpretation" claims unless absolutely necessary.

Never present an "insufficient" claim as an established fact.

Do not use Markdown code fences.

Do not include anything outside the JSON object.
"""


def format_evidence(context: AIContextResponse) -> str:
    sections = []

    for item in context.evidence:
        section = f"""
[Evidence {item.evidence_number}]
Type: {item.result_type}
Reference: {item.reference}
Title: {item.title}
Collection: {item.collection}
Book: {item.book_name}
Narrator: {item.narrator}

Arabic:
{item.text_arabic}

English translation:
{item.translation}

Translator:
{item.translator}

Source:
{item.source_name}

Author:
{item.source_author}

Publisher:
{item.source_publisher}

Source URL:
{item.source_url}

License:
{item.source_license}

Version:
{item.source_version}

Provenance:
{item.source_provenance}
"""
        sections.append(section)

    return "\n".join(sections)


def generate_initial_answer(
    context: AIContextResponse,
) -> dict:
    evidence_text = format_evidence(context)

    user_prompt = f"""
Question:
{context.question}

Burhān evidence:

{evidence_text}

Answer the question using only the evidence above.

Use [Evidence N] citations in the answer.

Then extract the important factual claims from your answer.

For every claim:
- classify it as "explicit", "interpretation", or "insufficient"
- provide the evidence numbers that support it

Return ONLY the required JSON object.
"""

    raw_answer = generate_answer(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    try:
        return json.loads(raw_answer)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")


def revise_answer(
    context: AIContextResponse,
    answer: str,
    issues: list,
) -> dict:
    evidence_text = format_evidence(context)

    issue_text = ""

    for issue in issues:
        issue_text += f"""
Problematic sentence:
{issue.sentence}

Reason it failed grounding:
{issue.reason}

"""

    user_prompt = f"""
Question:
{context.question}

Original AI answer:
{answer}

Grounding validator findings:

{issue_text}

Burhān evidence:

{evidence_text}

Revise the original answer so that every factual sentence is directly
supported by the supplied evidence.

Remove unsupported claims.

Narrow overextended statements instead of adding new information.

When a sentence cannot be made directly supported, DELETE it.

When in doubt, DELETE the sentence.

Do not use outside knowledge.

Keep [Evidence N] citations.

Return ONLY the required JSON object.
"""

    raw_revision = generate_answer(
        system_prompt=REVISION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    try:
        return json.loads(raw_revision)
    except json.JSONDecodeError:
        raise ValueError("AI revision returned invalid JSON")


def build_claims(
    data: dict,
) -> list[AIAnswerClaim]:
    return [
        AIAnswerClaim(
            claim=claim["claim"],
            support_level=claim["support_level"],
            evidence_numbers=claim["evidence_numbers"],
            grounded=False,
            grounding_reason="Pending semantic grounding validation.",
        )
        for claim in data.get("claims", [])
    ]


def build_evidence(
    context: AIContextResponse,
) -> list[AIAnswerEvidence]:
    return [
        AIAnswerEvidence(
            evidence_number=item.evidence_number,
            reference=item.reference,
            result_type=item.result_type,
        )
        for item in context.evidence
    ]


def validate_claims(
    claims: list[AIAnswerClaim],
    context: AIContextResponse,
) -> list[AIAnswerClaim]:
    grounded_claims = []

    for claim in claims:
        validation = validate_claim(
            claim=claim,
            context=context,
        )

        grounded_claims.append(
            AIAnswerClaim(
                claim=claim.claim,
                support_level=claim.support_level,
                evidence_numbers=claim.evidence_numbers,
                grounded=validation.grounded,
                grounding_reason=validation.reason,
            )
        )

    return grounded_claims


def validate_generated_answer(
    answer: str,
    claims: list[AIAnswerClaim],
    context: AIContextResponse,
):
    validate_ai_answer(
        AIAnswerResponse(
            question=context.question,
            answer=answer,
            answer_grounded=False,
            answer_grounding_issues=[],
            claims=claims,
            evidence=build_evidence(context),
        )
    )

    grounded_claims = validate_claims(
        claims=claims,
        context=context,
    )

    answer_validation = validate_answer(
        answer=answer,
        context=context,
    )

    return grounded_claims, answer_validation


def build_ai_answer(
    context: AIContextResponse,
) -> AIAnswerResponse:

    # ---------------------------------------------------------
    # First generation
    # ---------------------------------------------------------

    data = generate_initial_answer(context)

    answer = data["answer"]
    claims = build_claims(data)

    grounded_claims, answer_validation = validate_generated_answer(
        answer=answer,
        claims=claims,
        context=context,
    )

    # ---------------------------------------------------------
    # Automatic revision
    # ---------------------------------------------------------

    if not answer_validation.grounded:

        revised_data = revise_answer(
            context=context,
            answer=answer,
            issues=answer_validation.issues,
        )

        answer = revised_data["answer"]
        claims = build_claims(revised_data)

        grounded_claims, answer_validation = validate_generated_answer(
            answer=answer,
            claims=claims,
            context=context,
        )

    # ---------------------------------------------------------
    # Final hard gate
    # ---------------------------------------------------------

    if not answer_validation.grounded:
        raise ValueError(
            {
                "message": "AI answer failed final grounding validation",
                "issues": [
                    {
                        "sentence": issue.sentence,
                        "reason": issue.reason,
                    }
                    for issue in answer_validation.issues
                ],
            }
        )

    return AIAnswerResponse(
        question=context.question,
        answer=answer,
        answer_grounded=True,
        answer_grounding_issues=[],
        claims=grounded_claims,
        evidence=build_evidence(context),
    )