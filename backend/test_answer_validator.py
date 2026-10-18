from app.services.answer_validator import validate_answer
from app.schemas.ai_context import AIContextResponse, AIContextEvidence


context = AIContextResponse(
    question="mercy",
    evidence=[
        AIContextEvidence(
            evidence_number=1,
            result_type="quran",
            reference="7:151",
            title="Al-A'raf",
            collection=None,
            book_number=None,
            book_name=None,
            narrator=None,
            text_arabic="وَأَدْخِلْنَا فِي رَحْمَتِكَ وَأَنتَ خَيْرُ الرَّاحِمِينَ",
            translation="And admit us into Your mercy, for You are the Most Merciful of the merciful.",
            translator="Talal Itani",
            source_name="ClearQuran",
            source_author="Talal Itani",
            source_publisher="ClearQuran.com",
            source_url="https://www.clearquran.com/",
            source_license="CC BY-ND 4.0",
            source_version="Edition Allah",
            source_provenance="Official ClearQuran distribution.",
        )
    ],
)


bad_answer = """
Allah is the Most Merciful of the merciful.

Therefore, Islam teaches that Muslims who commit major sins
will definitely be forgiven by Allah.
"""


result = validate_answer(
    answer=bad_answer,
    context=context,
)


print("Grounded:", result.grounded)
print()

if result.issues:
    print("Issues:")
    for issue in result.issues:
        print("-", issue.sentence)
        print("  Reason:", issue.reason)
else:
    print("No issues detected.")