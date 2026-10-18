import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.evidence_sets import build_evidence_item_response
from app.db.session import SessionLocal
from app.models.ayah import Ayah
from app.models.evidence_item import EvidenceItem
from app.models.evidence_set import EvidenceSet
from app.models.hadith import Hadith
from app.models.hadith_book import HadithBook
from app.models.hadith_collection import HadithCollection
from app.models.hadith_translation import HadithTranslation
from app.models.source import Source
from app.models.surah import Surah
from app.models.translation import Translation
from app.schemas.ayah import AyahWithTranslationsResponse
from app.schemas.evidence_set import EvidenceSetResponse
from app.schemas.hadith import HadithResponse
from app.schemas.research import ResearchResponse
from app.services.arabic import normalize_arabic


router = APIRouter(prefix="/search", tags=["Research"])


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Qur'an reference parsing
# ---------------------------------------------------------------------------

AYAH_REFERENCE_PATTERN = re.compile(r"^\s*(\d{1,3})\s*:\s*(\d{1,3})\s*$")


def parse_ayah_reference(query: str) -> tuple[int, int] | None:
    """
    Parse queries like "52:35" into (surah_number, ayah_number).
    Returns None if the query is not a valid-looking reference.
    """
    match = AYAH_REFERENCE_PATTERN.match(query)

    if not match:
        return None

    surah_number = int(match.group(1))
    ayah_number = int(match.group(2))

    if not (1 <= surah_number <= 114) or ayah_number < 1:
        return None

    return surah_number, ayah_number
# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------


def normalize_arabic_for_search(text: str | None) -> str:
    if not text:
        return ""

    normalized = normalize_arabic(text)

    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_search_text(text: str | None) -> str:
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[.!?]+", ". ", text)
    text = re.sub(r"[:;]+", " ", text)
    text = re.sub(r'["“”‘’]+', " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_arabic(text: str | None) -> bool:
    if not text:
        return False

    return bool(re.search(r"[\u0600-\u06FF]", text))


def contains_query(query: str, text: str) -> bool:
    query_normalized = normalize_search_text(query)
    text_normalized = normalize_search_text(text)

    if not query_normalized or not text_normalized:
        return False

    return query_normalized in text_normalized


# ---------------------------------------------------------------------------
# Sentence/context helpers
# ---------------------------------------------------------------------------


def _sentence_boundaries(text: str) -> list[str]:
    normalized = normalize_search_text(text)

    if not normalized:
        return []

    sentences = re.split(r"[.!?]+", normalized)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def query_sentence_contexts(
    query: str,
    text: str,
) -> list[str]:
    normalized_query = normalize_search_text(query)

    if not normalized_query:
        return []

    contexts = []

    for sentence in _sentence_boundaries(text):
        if normalized_query in sentence:
            contexts.append(sentence)

    return contexts


def query_local_contexts(
    query: str,
    text: str,
    window: int = 120,
) -> list[str]:
    normalized_query = normalize_search_text(query)
    normalized_text = normalize_search_text(text)

    if not normalized_query or not normalized_text:
        return []

    contexts = []

    for match in re.finditer(
        re.escape(normalized_query),
        normalized_text,
    ):
        start = max(0, match.start() - window)
        end = min(len(normalized_text), match.end() + window)

        contexts.append(normalized_text[start:end])

    return contexts


def query_matches_sentence_regex(
    text: str,
    patterns: list[str],
) -> bool:
    for sentence in _sentence_boundaries(text):
        for pattern in patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                return True

    return False


def query_matches_long_range_regex(
    text: str,
    patterns: list[str],
    max_chars: int = 600,
) -> bool:
    normalized = normalize_search_text(text)

    if not normalized:
        return False

    for pattern in patterns:
        if re.search(
            pattern,
            normalized[: max_chars + 1],
            re.IGNORECASE,
        ):
            return True

    return False


# ---------------------------------------------------------------------------
# Search aliases
# ---------------------------------------------------------------------------


SEARCH_CONCEPT_ALIASES = {
    "zina": [
        "adultery",
        "fornication",
    ],
    "riba": [
        "usury",
        "interest",
    ],
    "salah": [
        "salat",
        "prayer",
        "prayers",
    ],
    "salat": [
        "salah",
        "prayer",
        "prayers",
    ],
    "sawm": [
        "siyam",
        "fasting",
        "fast",
    ],
    "siyam": [
        "sawm",
        "fasting",
        "fast",
    ],
    "zakat": [
        "charity",
        "alms",
        "almsgiving",
    ],
    "wudu": [
        "wudhu",
        "ablution",
        "ablutions",
    ],
    "wudhu": [
        "wudu",
        "ablution",
        "ablutions",
    ],
    "ghusl": [
        "ritual bath",
        "ritual bathing",
    ],
    "hajj": [
        "pilgrimage",
    ],
    "umrah": [
        "pilgrimage",
    ],
    "shirk": [
        "polytheism",
        "idolatry",
        "associating partners",
    ],
    "tawhid": [
        "monotheism",
        "oneness of god",
        "oneness of Allah",
    ],
    "iman": [
        "faith",
        "belief",
    ],
    "kufr": [
        "disbelief",
        "unbelief",
    ],
    "hijab": [
        "veil",
        "veiling",
    ],
    "awrah": [
        "private parts",
        "nakedness",
    ],
    "mahr": [
        "dowry",
    ],
    "nikah": [
        "marriage",
        "marriage contract",
    ],
    "talak": [
        "talaq",
        "divorce",
    ],
    "talaq": [
        "talak",
        "divorce",
    ],
    "wasiyyah": [
        "will",
        "bequest",
    ],
    "sadaqah": [
        "sadaqa",
        "charity",
        "alms",
    ],
    "sadaqa": [
        "sadaqah",
        "charity",
        "alms",
    ],
    "khamr": [
        "alcohol",
        "wine",
        "intoxicants",
    ],
    "khmar": [
        "alcohol",
        "wine",
        "intoxicants",
    ],
    "maysir": [
        "gambling",
    ],
}


def expand_search_terms(query: str) -> list[str]:
    normalized = normalize_search_text(query)

    if not normalized:
        return []

    terms = [normalized]

    if normalized in SEARCH_CONCEPT_ALIASES:
        terms.extend(
            SEARCH_CONCEPT_ALIASES[normalized]
        )

    # For multi-word queries, also expand individual concepts.
    words = normalized.split()

    for word in words:
        aliases = SEARCH_CONCEPT_ALIASES.get(word)

        if aliases:
            terms.extend(aliases)

    # Preserve order while removing duplicates.
    seen = set()
    result = []

    for term in terms:
        normalized_term = normalize_search_text(term)

        if not normalized_term:
            continue

        if normalized_term not in seen:
            seen.add(normalized_term)
            result.append(normalized_term)

    return result


def _english_retrieval_variants(
    terms: list[str],
) -> list[str]:
    variants = []

    for term in terms:
        normalized = normalize_search_text(term)

        if not normalized:
            continue

        variants.append(normalized)

        words = normalized.split()

        if len(words) > 1:
            variants.extend(words)

    seen = set()
    result = []

    for variant in variants:
        if variant not in seen:
            seen.add(variant)
            result.append(variant)

    return result


def expanded_english_tsquery(
    column,
    terms: list[str],
):
    variants = _english_retrieval_variants(terms)

    expressions = []

    for variant in variants:
        expressions.append(
            func.plainto_tsquery(
                "english",
                variant,
            )
        )

    if not expressions:
        return None

    expression = column.op("@@")(
        expressions[0]
    )

    for query_expression in expressions[1:]:
        expression = or_(
            expression,
            column.op("@@")(
                query_expression
            ),
        )

    return expression


def expanded_english_rank(
    column,
    terms: list[str],
):
    variants = _english_retrieval_variants(terms)

    ranks = []

    for variant in variants:
        ranks.append(
            func.ts_rank_cd(
                func.to_tsvector(
                    "english",
                    column,
                ),
                func.plainto_tsquery(
                    "english",
                    variant,
                ),
            )
        )

    if not ranks:
        return 0.0

    expression = ranks[0]

    for rank in ranks[1:]:
        expression = func.greatest(
            expression,
            rank,
        )

    return expression


# ---------------------------------------------------------------------------
# Evidence roles
# ---------------------------------------------------------------------------


EVIDENCE_ROLE_PRIORITY = {
    "direct": 6,
    "consequence": 5,
    "conceptual": 4,
    "contextual": 3,
    "related": 2,
    "incidental": 1,
}


EVIDENCE_ROLE_BASE_SCORES = {
    "direct": 0.68,
    "consequence": 0.58,
    "conceptual": 0.52,
    "contextual": 0.46,
    "related": 0.27,
    "incidental": 0.05,
}


EVIDENCE_ROLE_WEIGHTS = {
    "direct": 0.32,
    "consequence": 0.28,
    "conceptual": 0.26,
    "contextual": 0.24,
    "related": 0.20,
    "incidental": 0.10,
}


# ---------------------------------------------------------------------------
# Evidence classification
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Query intent
# ---------------------------------------------------------------------------


def detect_query_intent(query: str) -> str:
    """
    Determine what the user is asking for.

    This is deliberately lightweight. It is not trying to understand the
    entire question semantically; it only identifies the type of answer
    being requested so that evidence can be ranked appropriately.
    """

    normalized = normalize_search_text(query)

    if not normalized:
        return "general"

    # Consequence / punishment
    if re.search(
        r"\b(?:punishment|punished|penalty|penalties|"
        r"penalized|consequence|consequences|reward|rewarded|"
        r"hell|hellfire|warning|threat|threatened|curse|cursed)\b",
        normalized,
        re.IGNORECASE,
    ):
        return "consequence"

    # Concept / definition
    if re.search(
        r"\b(?:what is|what are|what does|what do|"
        r"meaning|definition|define|refers to|refers|means)\b",
        normalized,
        re.IGNORECASE,
    ):
        return "conceptual"

    # Context
    if re.search(
        r"\b(?:context|background|occasion|revelation|"
        r"why was|why did|why does|before|after|previous|"
        r"following|preceding|historical context)\b",
        normalized,
        re.IGNORECASE,
    ):
        return "contextual"

    # Explicit ruling question
    if re.search(
        r"\b(?:is|are|was|were)\b.*\b(?:forbidden|prohibited|"
        r"unlawful|illegal|haram|permitted|lawful|legal|halal|"
        r"allowed|permissible|obligatory|required)\b",
        normalized,
        re.IGNORECASE,
    ):
        return "ruling"

    if re.search(
        r"\b(?:forbidden|prohibited|unlawful|illegal|haram|"
        r"permitted|lawful|legal|halal|allowed|permissible|"
        r"obligatory|required|ruling|verdict)\b",
        normalized,
        re.IGNORECASE,
    ):
        return "ruling"

    return "general"


def detect_arabic_query_intent(query: str) -> str:
    normalized = normalize_arabic_for_search(query)

    if not normalized:
        return "general"

    if re.search(
        r"(عقاب|عذاب|جزاء|ثواب|أجر|حد|وعيد|تهديد|لعن|لعنة|نار|جهنم)",
        normalized,
    ):
        return "consequence"

    if re.search(
        r"(ما هو|ما هي|ما معنى|معنى|تعريف|يعني|ما المقصود)",
        normalized,
    ):
        return "conceptual"

    if re.search(
        r"(سياق|سبب النزول|لماذا|قبل|بعد|السابق|التالي)",
        normalized,
    ):
        return "contextual"

    if re.search(
        r"(حكم|حرام|حلال|فرض|واجب|يجوز|لا يجوز|لا يحل|ممنوع)",
        normalized,
    ):
        return "ruling"

    return "general"


# ---------------------------------------------------------------------------
# Evidence classification
# ---------------------------------------------------------------------------


DIRECT_RULING_PATTERNS = [
    r"\b(?:forbidden|prohibited|unlawful|illegal|haram)\b",
    r"\b(?:permitted|lawful|legal|halal|allowed|permissible)\b",
    r"\b(?:commanded|command|ordered)\b",
    r"\b(?:required|obligatory|obligation)\b",
    r"\b(?:ruling|verdict)\b",
]

CONSEQUENCE_PATTERNS = [
    r"\bpunish(?:ed|ment|es|ing)?\b",
    r"\bpunishment\b",
    r"\bpenalt(?:y|ies)\b",
    r"\bwarn(?:ed|ing)?\b",
    r"\bwarning\b",
    r"\bthreat(?:ened|ening)?\b",
    r"\bcurse(?:d)?\b",
    r"\bcursed\b",
    r"\bhellfire\b",
    r"\bhell\b",
    r"\bpainful punishment\b",
    r"\breward(?:ed|s)?\b",
]

CONCEPTUAL_PATTERNS = [
    r"\b(?:means|mean|meaning)\b",
    r"\b(?:refers to|refer to)\b",
    r"\b(?:defined as|definition)\b",
    r"\b(?:is called|are called)\b",
    r"\b(?:is known as|are known as)\b",
    r"\b(?:includes|include)\b",
    r"\b(?:consists of|consist of)\b",
    r"\b(?:forms of|types of|kinds of)\b",
]

CONTEXTUAL_PATTERNS = [
    r"\b(?:previous|preceding|earlier)\s+(?:verse|ayah|passage)\b",
    r"\b(?:following|next)\s+(?:verse|ayah|passage)\b",
    r"\b(?:context|contextual)\b",
    r"\b(?:occasion of revelation|revelation)\b",
]


ARABIC_DIRECT_PATTERNS = [
    r"(حرام|حرمة|حرم)",
    r"(فرض|فريضة|واجب|وجوب)",
    r"(أوجب|امر|أمر)",
    r"(نهى|نهي|منع|ممنوع)",
    r"(لا يجوز|لا يحل|لا تحل)",
    r"(يجوز|يحل|حلال)",
]

ARABIC_CONSEQUENCE_PATTERNS = [
    r"(عذاب|يعذب|عقاب|يعاقب)",
    r"(نار|جهنم)",
    r"(لعن|لعنة|ملعون)",
    r"(ثواب|أجر|جزاء)",
    r"(وعيد|توعد)",
]

ARABIC_CONCEPTUAL_PATTERNS = [
    r"(يعني|معنى|معناه)",
    r"(يسمى|تسمى|يطلق عليه)",
    r"(أنواع|أقسام)",
]

ARABIC_CONTEXTUAL_PATTERNS = [
    r"(سبب النزول|سياق|السياق)",
    r"(قبل|بعد|السابقة|التالية)",
]


def _query_terms_present(
    query: str,
    text: str,
) -> list[str]:
    """
    Return the search terms that actually occur in the text.

    The original query is preferred, while aliases can contribute to
    classification because Qur'an translations may say "adultery" rather
    than "zina", etc.
    """

    normalized_text = normalize_search_text(text)
    terms = expand_search_terms(query)

    matches = []

    for term in terms:
        normalized_term = normalize_search_text(term)

        if normalized_term and normalized_term in normalized_text:
            matches.append(normalized_term)

    return matches


def _is_exceptional_or_conditional_mention(
    sentence: str,
    term: str,
) -> bool:
    """
    Detect whether the requested term itself appears inside an
    exception or condition.

    The exception/condition must remain within the same clause as
    the requested term. This prevents an unrelated "except" earlier
    in a sentence from contaminating a separate ruling clause.
    """

    escaped_term = re.escape(term)

    patterns = [
        # "unless they commit adultery"
        rf"\b(?:unless|except)\b"
        rf"(?:(?!\b(?:do not|don't)\b).){{0,50}}"
        rf"\b{escaped_term}\b",

        # "if they commit adultery"
        rf"\b(?:if|when|whenever|provided that)\b"
        rf"(?:(?!\b(?:do not|don't)\b).){{0,50}}"
        rf"\b{escaped_term}\b",

        # "adultery, if ..."
        rf"\b{escaped_term}\b"
        rf"[^.?!]{{0,50}}"
        rf"\b(?:if|when|whenever|provided that)\b",
    ]

    return any(
        re.search(
            pattern,
            sentence,
            re.IGNORECASE,
        )
        for pattern in patterns
    )

def _has_direct_ruling_tied_to_term(
    sentence: str,
    term: str,
) -> bool:
    """
    A ruling must be tied to the requested concept.

    This prevents a sentence such as:

        Do not coerce them ... unless they commit adultery.

    from being classified as direct evidence for "zina" merely because
    "do not" appears somewhere in the sentence.
    """

    escaped_term = re.escape(term)

    if _is_exceptional_or_conditional_mention(
        sentence,
        term,
    ):
        return False

    patterns = [
        # "do not commit adultery"
        rf"\b(?:do not|don't)\b[^.?!]{{0,80}}\b{escaped_term}\b",

        # "do not come near adultery"
        rf"\b(?:do not|don't)\b[^.?!]{{0,80}}\b{escaped_term}\b",

        # "adultery is forbidden"
        rf"\b{escaped_term}\b[^.?!]{{0,80}}"
        rf"\b(?:is|are|was|were)\b[^.?!]{{0,40}}"
        rf"\b(?:forbidden|prohibited|unlawful|illegal|haram)\b",

        # "adultery is not permitted"
        rf"\b{escaped_term}\b[^.?!]{{0,80}}"
        rf"\b(?:is|are|was|were)\b[^.?!]{{0,40}}"
        rf"\b(?:not permitted|not allowed|unlawful|illegal)\b",

        # "forbidden adultery"
        rf"\b(?:forbidden|prohibited|unlawful|illegal|haram)\b"
        rf"[^.?!]{{0,40}}\b{escaped_term}\b",
    ]

    return any(
        re.search(
            pattern,
            sentence,
            re.IGNORECASE,
        )
        for pattern in patterns
    )


def _has_consequence_tied_to_term(
    sentence: str,
    term: str,
) -> bool:
    escaped_term = re.escape(term)

    if not re.search(
        rf"\b{escaped_term}\b",
        sentence,
        re.IGNORECASE,
    ):
        return False

    return any(
        re.search(
            pattern,
            sentence,
            re.IGNORECASE,
        )
        for pattern in CONSEQUENCE_PATTERNS
    )


def classify_evidence_role(
    query: str,
    text: str,
    source_type: str | None = None,
) -> str:
    if not query or not text:
        return "incidental"

    # -----------------------------------------------------------------------
    # Arabic
    # -----------------------------------------------------------------------

    if contains_arabic(query):
        normalized_query = normalize_arabic_for_search(query)
        normalized_text = normalize_arabic_for_search(text)

        if not normalized_query or not normalized_text:
            return "incidental"

        if normalized_query not in normalized_text:
            return "incidental"

        intent = detect_arabic_query_intent(query)

        if intent == "consequence":
            if any(
                re.search(
                    pattern,
                    normalized_text,
                )
                for pattern in ARABIC_CONSEQUENCE_PATTERNS
            ):
                return "consequence"

        if intent == "ruling":
            if any(
                re.search(
                    pattern,
                    normalized_text,
                )
                for pattern in ARABIC_DIRECT_PATTERNS
            ):
                return "direct"

        if intent == "conceptual":
            if any(
                re.search(
                    pattern,
                    normalized_text,
                )
                for pattern in ARABIC_CONCEPTUAL_PATTERNS
            ):
                return "conceptual"

        if intent == "contextual":
            if any(
                re.search(
                    pattern,
                    normalized_text,
                )
                for pattern in ARABIC_CONTEXTUAL_PATTERNS
            ):
                return "contextual"

        # General Arabic query.
        if any(
            re.search(
                pattern,
                normalized_text,
            )
            for pattern in ARABIC_CONSEQUENCE_PATTERNS
        ):
            return "consequence"

        if any(
            re.search(
                pattern,
                normalized_text,
            )
            for pattern in ARABIC_DIRECT_PATTERNS
        ):
            return "direct"

        return "related"

    # -----------------------------------------------------------------------
    # English
    # -----------------------------------------------------------------------

    normalized_query = normalize_search_text(query)
    normalized_text = normalize_search_text(text)

    if not normalized_query or not normalized_text:
        return "incidental"

    matching_terms = _query_terms_present(
        query,
        text,
    )

    if not matching_terms:
        return "incidental"

    intent = detect_query_intent(query)
    sentences = _sentence_boundaries(text)

    # Evaluate the most specific evidence role first.
    for sentence in sentences:
        sentence_terms = [
            term
            for term in matching_terms
            if term in sentence
        ]

        if not sentence_terms:
            continue

        for term in sentence_terms:
            if intent == "consequence":
                if _has_consequence_tied_to_term(
                    sentence,
                    term,
                ):
                    return "consequence"

            if intent == "ruling":
                if _has_direct_ruling_tied_to_term(
                    sentence,
                    term,
                ):
                    return "direct"

            if intent == "conceptual":
                if any(
                    re.search(
                        pattern,
                        sentence,
                        re.IGNORECASE,
                    )
                    for pattern in CONCEPTUAL_PATTERNS
                ):
                    return "conceptual"

            if intent == "contextual":
                if any(
                    re.search(
                        pattern,
                        sentence,
                        re.IGNORECASE,
                    )
                    for pattern in CONTEXTUAL_PATTERNS
                ):
                    return "contextual"

    # General query: infer the role from the passage itself.
    for sentence in sentences:
        sentence_terms = [
            term
            for term in matching_terms
            if term in sentence
        ]

        if not sentence_terms:
            continue

        for term in sentence_terms:
            if _has_consequence_tied_to_term(
                sentence,
                term,
            ):
                return "consequence"

            if _has_direct_ruling_tied_to_term(
                sentence,
                term,
            ):
                return "direct"

    # A definition/contextual pattern can still be useful even when the
    # user asked a broad concept query.
    if intent == "conceptual":
        return "conceptual"

    if intent == "contextual":
        return "contextual"

    return "related"

# ---------------------------------------------------------------------------
# Lexical relevance
# ---------------------------------------------------------------------------


def lexical_relevance_score(
    query: str,
    text: str,
) -> float:
    if not query or not text:
        return 0.0

    if contains_arabic(query):
        normalized_query = normalize_arabic_for_search(query)
        normalized_text = normalize_arabic_for_search(text)

        if not normalized_query or not normalized_text:
            return 0.0

        if normalized_query == normalized_text:
            return 1.0

        if normalized_query in normalized_text:
            return 1.0

        query_tokens = normalized_query.split()

        if not query_tokens:
            return 0.0

        matched = sum(
            1
            for token in query_tokens
            if token in normalized_text
        )

        ratio = matched / len(query_tokens)

        if ratio == 1.0:
            return 0.90

        if ratio > 0:
            return 0.55 + (0.35 * ratio)

        return 0.0

    normalized_query = normalize_search_text(query)
    normalized_text = normalize_search_text(text)

    if not normalized_query or not normalized_text:
        return 0.0

    if normalized_query == normalized_text:
        return 1.0

    if normalized_query in normalized_text:
        return 1.0

    query_tokens = normalized_query.split()

    if not query_tokens:
        return 0.0

    matched = sum(
        1
        for token in query_tokens
        if re.search(
            rf"\b{re.escape(token)}\b",
            normalized_text,
        )
    )

    ratio = matched / len(query_tokens)

    if ratio == 1.0:
        return 0.90

    if ratio > 0:
        return 0.55 + (0.35 * ratio)

# Alias-aware fallback.
#
# An alias is useful for retrieval, but it is weaker
# than an exact query match because the text does not
# literally contain the user's requested term.
    for alias in SEARCH_CONCEPT_ALIASES.get(
    normalized_query,
    [],
):
     if normalize_search_text(alias) in normalized_text:
       return 0.45
    
    return 0.0


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def normalize_retrieval_score(
    retrieval_score: float,
) -> float:
    value = max(
        0.0,
        float(retrieval_score or 0.0),
    )

    if value <= 0.0:
        return 0.0

    normalized = 1.0 - (
        2.718281828 ** (-4.0 * value)
    )

    return max(
        0.0,
        min(1.0, normalized),
    )


def evidence_role_match_score(
    query: str,
    evidence_role: str,
) -> float:
    intent = detect_query_intent(query)

    expected_roles = {
        "ruling": {
            "direct": 1.0,
            "consequence": 0.35,
            "conceptual": 0.20,
            "contextual": 0.15,
            "related": 0.10,
            "incidental": 0.0,
        },
        "consequence": {
            "consequence": 1.0,
            "direct": 0.55,
            "conceptual": 0.15,
            "contextual": 0.15,
            "related": 0.10,
            "incidental": 0.0,
        },
        "conceptual": {
            "conceptual": 1.0,
            "direct": 0.40,
            "consequence": 0.20,
            "contextual": 0.25,
            "related": 0.15,
            "incidental": 0.0,
        },
        "contextual": {
            "contextual": 1.0,
            "conceptual": 0.35,
            "direct": 0.25,
            "consequence": 0.20,
            "related": 0.15,
            "incidental": 0.0,
        },
        "general": {
            "direct": 1.0,
            "consequence": 0.80,
            "conceptual": 0.70,
            "contextual": 0.55,
            "related": 0.35,
            "incidental": 0.0,
        },
    }

    return expected_roles.get(
        intent,
        expected_roles["general"],
    ).get(
        evidence_role,
        0.0,
    )

def calculate_research_score(
    retrieval_score: float,
    query: str,
    text: str,
    evidence_role: str,
) -> float:
    retrieval = normalize_retrieval_score(
        retrieval_score,
    )

    lexical = lexical_relevance_score(
        query,
        text,
    )

    role_match = evidence_role_match_score(
        query,
        evidence_role,
    )

    normalized_query = normalize_search_text(query)
    normalized_text = normalize_search_text(text)

    exactness = 0.0

    if normalized_query and normalized_query in normalized_text:
        exactness = 1.0
    elif lexical >= 0.90:
        exactness = 0.80
    elif lexical >= 0.70:
        exactness = 0.50
    elif lexical > 0:
        exactness = 0.25

    score = (
        (0.40 * retrieval)
        + (0.30 * lexical)
        + (0.20 * role_match)
        + (0.10 * exactness)
    )

    return round(
        max(
            0.0,
            min(1.0, score),
        ),
        6,
    )

# ---------------------------------------------------------------------------
# Source serialization
# ---------------------------------------------------------------------------


def build_source_response(
    source: Source | None,
) -> dict | None:
    if source is None:
        return None

    return {
        "id": source.id,
        "name": source.name,
        "slug": source.slug,
        "source_type": source.source_type,
        "language": source.language,
        "author": source.author,
        "publisher": source.publisher,
        "url": source.url,
        "license": source.license,
        "version": source.version,
        "provenance_note": source.provenance_note,
        "description": source.description,
    }


# ---------------------------------------------------------------------------
# Result identity / ranking
# ---------------------------------------------------------------------------


def evidence_identity_key(
    result: dict,
) -> tuple:
    source = result.get("primary_source")

    if source is None:
        source = result.get("source")

    source_id = (
        source.get("id")
        if source
        else None
    )

    return (
        result.get("result_type"),
        result.get("id"),
        source_id,
    )


def _ranking_key(
    result: dict,
) -> tuple:
    role = result.get(
        "evidence_role",
        "incidental",
    )

    priority = EVIDENCE_ROLE_PRIORITY.get(
        role,
        1,
    )

    score = float(
        result.get("score", 0.0)
    )

    # Score is the primary ranking factor.
    # Role acts as a controlled secondary factor instead of creating
    # absolute buckets where every "direct" result beats every
    # "consequence" result.
    role_bonus = priority * 0.008

    return (
        score + role_bonus,
        score,
        priority,
        -int(result.get("id", 0)),
    )


def rank_results(
    results: list[dict],
) -> list[dict]:
    return sorted(
        results,
        key=_ranking_key,
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Evidence selection
# ---------------------------------------------------------------------------


def select_evidence_results(
    results: list[dict],
    limit: int,
) -> list[dict]:
    if limit <= 0:
        return []

    deduplicated: dict[tuple, dict] = {}

    for result in results:
        key = evidence_identity_key(result)

        existing = deduplicated.get(key)

        if existing is None:
            deduplicated[key] = result
            continue

        if _ranking_key(result) > _ranking_key(existing):
            deduplicated[key] = result

    ranked = rank_results(
        list(deduplicated.values())
    )

    return ranked[:limit]


# ---------------------------------------------------------------------------
# Research result builders
# ---------------------------------------------------------------------------


def _build_quran_result(
    ayah: Ayah,
    surah: Surah,
    translation: Translation | None,
    translation_source: Source | None,
    primary_source: Source | None,
    query: str,
    retrieval_score: float,
) -> dict:
    translation_text = (
        translation.text
        if translation is not None
        else None
    )

    searchable_text = (
        translation_text
        if translation_text
        else ayah.text_arabic
    )

    evidence_role = classify_evidence_role(
        query=query,
        text=searchable_text,
        source_type="quran",
    )

    score = calculate_research_score(
        retrieval_score=retrieval_score,
        query=query,
        text=searchable_text,
        evidence_role=evidence_role,
    )

    return {
        "id": ayah.id,
        "result_type": "quran",
        "reference": f"{surah.number}:{ayah.number}",
        "title": surah.name_english,
        "collection": None,
        "book_number": None,
        "book_name": None,
        "narrator": None,
        "text_arabic": ayah.text_arabic,
        "translation": translation_text,
        "translator": (
            translation.translator
            if translation is not None
            else None
        ),
        "match_type": "full_text",
        "source": build_source_response(
            translation_source or primary_source
        ),
        "primary_source": build_source_response(
            primary_source
        ),
        "translation_source": build_source_response(
            translation_source
        ),
        "score": score,
        "evidence_role": evidence_role,
    }


def _build_hadith_result(
    hadith: Hadith,
    book: HadithBook,
    collection: HadithCollection,
    translation: HadithTranslation | None,
    source: Source | None,
    translation_source: Source | None,
    query: str,
    retrieval_score: float,
) -> dict:
    translation_text = (
        translation.text
        if translation is not None
        else None
    )

    searchable_text = (
        translation_text
        if translation_text
        else hadith.text_arabic
    )

    evidence_role = classify_evidence_role(
        query=query,
        text=searchable_text,
        source_type="hadith",
    )

    score = calculate_research_score(
        retrieval_score=retrieval_score,
        query=query,
        text=searchable_text,
        evidence_role=evidence_role,
    )

    return {
        "id": hadith.id,
        "result_type": "hadith",
        "reference": hadith.reference,
        "title": None,
        "collection": collection.name,
        "book_number": book.number,
        "book_name": book.name,
        "narrator": hadith.narrator,
        "text_arabic": hadith.text_arabic,
        "translation": translation_text,
        "translator": (
            translation.translator
            if translation is not None
            else None
        ),
        "match_type": "full_text",
        "source": build_source_response(
            source
        ),
        "primary_source": build_source_response(
            source
        ),
        "translation_source": build_source_response(
            translation_source
        ),
        "score": score,
        "evidence_role": evidence_role,
    }


# ---------------------------------------------------------------------------
# Main research search
# ---------------------------------------------------------------------------


@router.get(
    "/research",
    response_model=ResearchResponse,
)
def research_search(
    q: str = Query(
        ...,
        min_length=1,
    ),
    domain: str = Query(
        "quran",
        pattern="^(quran|hadith)$",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    results: list[dict] = []

    # -----------------------------------------------------------------------
    # Qur'an
    # -----------------------------------------------------------------------

    if domain == "quran":
        quran_source = (
            db.query(Source)
            .filter(
                Source.source_type == "quran",
                Source.language == "ar",
            )
            .order_by(Source.id.asc())
            .first()
        )

        # Direct reference lookup, e.g. "52:35"
        ayah_reference = parse_ayah_reference(query)

        reference_row = None

        if ayah_reference:
            reference_surah_number, reference_ayah_number = ayah_reference

            reference_row = (
                db.query(Ayah, Surah)
                .join(
                    Surah,
                    Ayah.surah_id == Surah.id,
                )
                .filter(
                    Surah.number == reference_surah_number,
                    Ayah.number == reference_ayah_number,
                )
                .first()
            )

        if reference_row is not None:
            reference_ayah, reference_surah = reference_row

            # Prefer an English translation; fall back to any translation.
            reference_translation_row = (
                db.query(Translation, Source)
                .outerjoin(
                    Source,
                    Translation.source_id == Source.id,
                )
                .filter(Translation.ayah_id == reference_ayah.id)
                .order_by(
                    (Translation.language == "en").desc(),
                    Translation.id.asc(),
                )
                .first()
            )

            reference_translation = None
            reference_translation_source = None

            if reference_translation_row is not None:
                (
                    reference_translation,
                    reference_translation_source,
                ) = reference_translation_row

            reference_result = _build_quran_result(
                ayah=reference_ayah,
                surah=reference_surah,
                translation=reference_translation,
                translation_source=reference_translation_source,
                primary_source=quran_source,
                query=query,
                retrieval_score=1.0,
            )

            reference_result["match_type"] = "reference"
            reference_result["evidence_role"] = "direct"
            reference_result["score"] = 1.0

            results.append(reference_result)

        elif contains_arabic(query):
            normalized_query = normalize_arabic_for_search(
                query
            )

            if normalized_query:
                normalized_ayah_text = func.regexp_replace(
                    func.regexp_replace(
                        func.regexp_replace(
                            func.regexp_replace(
                                func.regexp_replace(
                                    Ayah.text_arabic,
                                    r"[\u064B-\u065F\u0670]",
                                    "",
                                ),
                                "أ",
                                "ا",
                            ),
                            "إ",
                            "ا",
                        ),
                        "آ",
                        "ا",
                    ),
                    "ٱ",
                    "ا",
                )

                normalized_ayah_text = func.regexp_replace(
                    normalized_ayah_text,
                    r"[[:space:][:punct:]]+",
                    "",
                )

                normalized_query_sql = re.sub(
                    r"[\s\W_]+",
                    "",
                    normalized_query,
                    flags=re.UNICODE,
                )

                ayahs = (
                    db.query(
                        Ayah,
                        Surah,
                        Translation,
                        Source,
                    )
                    .join(
                        Surah,
                        Ayah.surah_id == Surah.id,
                    )
                    .outerjoin(
                        Translation,
                        Translation.ayah_id == Ayah.id,
                    )
                    .outerjoin(
                        Source,
                        Translation.source_id == Source.id,
                    )
                    .filter(
                        normalized_ayah_text.contains(
                            normalized_query_sql
                        )
                    )
                    .order_by(
                        Ayah.id.asc(),
                        Translation.id.asc(),
                    )
                    .all()
                )

                for (
                    ayah,
                    surah,
                    translation,
                    translation_source,
                ) in ayahs:
                    result = _build_quran_result(
                        ayah=ayah,
                        surah=surah,
                        translation=translation,
                        translation_source=translation_source,
                        primary_source=quran_source,
                        query=query,
                        retrieval_score=1.0,
                    )

                    results.append(result)

        else:
            search_terms = expand_search_terms(
                query
            )

            english_match = expanded_english_tsquery(
                Translation.text,
                search_terms,
            )

            english_rank = expanded_english_rank(
                Translation.text,
                search_terms,
            )

            if english_match is not None:
                rows = (
                    db.query(
                        Ayah,
                        Surah,
                        Translation,
                        Source,
                    )
                    .join(
                        Surah,
                        Ayah.surah_id == Surah.id,
                    )
                    .join(
                        Translation,
                        Translation.ayah_id == Ayah.id,
                    )
                    .join(
                        Source,
                        Translation.source_id == Source.id,
                    )
                    .filter(
                        Translation.language == "en",
                        english_match,
                    )
                    .order_by(
                        english_rank.desc(),
                        Ayah.id.asc(),
                    )
                    .all()
                )

                for (
                    ayah,
                    surah,
                    translation,
                    translation_source,
                ) in rows:
                    retrieval_score = float(
                        translation_score
                        if (
                            translation_score := db.query(
                                func.ts_rank_cd(
                                    func.to_tsvector(
                                        "english",
                                        translation.text,
                                    ),
                                    func.plainto_tsquery(
                                        "english",
                                        query,
                                    ),
                                )
                            )
                            .scalar()
                        )
                        else 0.0
                    )

                    result = _build_quran_result(
                        ayah=ayah,
                        surah=surah,
                        translation=translation,
                        translation_source=translation_source,
                        primary_source=quran_source,
                        query=query,
                        retrieval_score=retrieval_score,
                    )

                    results.append(result)

    # -----------------------------------------------------------------------
    # Hadith
    # -----------------------------------------------------------------------

    else:
        if contains_arabic(query):
            normalized_query = normalize_arabic_for_search(
                query
            )

            normalized_hadith_text = func.regexp_replace(
                func.regexp_replace(
                    func.regexp_replace(
                        func.regexp_replace(
                            func.regexp_replace(
                                Hadith.text_arabic,
                                r"[\u064B-\u065F\u0670]",
                                "",
                            ),
                            "أ",
                            "ا",
                        ),
                        "إ",
                        "ا",
                    ),
                    "آ",
                    "ا",
                ),
                "ٱ",
                "ا",
            )

            normalized_hadith_text = func.regexp_replace(
                normalized_hadith_text,
                r"[[:space:][:punct:]]+",
                "",
            )

            normalized_query_sql = re.sub(
                r"[\s\W_]+",
                "",
                normalized_query,
                flags=re.UNICODE,
            )

            rows = (
                db.query(
                    Hadith,
                    HadithBook,
                    HadithCollection,
                    HadithTranslation,
                    Source,
                )
                .join(
                    HadithBook,
                    Hadith.book_id == HadithBook.id,
                )
                .join(
                    HadithCollection,
                    HadithBook.collection_id
                    == HadithCollection.id,
                )
                .outerjoin(
                    HadithTranslation,
                    HadithTranslation.hadith_id
                    == Hadith.id,
                )
                .join(
                    Source,
                    HadithCollection.source_id
                    == Source.id,
                )
                .filter(
                    normalized_hadith_text.contains(
                        normalized_query_sql
                    )
                )
                .order_by(
                    Hadith.id.asc(),
                    HadithTranslation.id.asc(),
                )
                .all()
            )

            for (
                hadith,
                book,
                collection,
                translation,
                source,
            ) in rows:
                translation_source = None

                if translation is not None:
                    translation_source = None

                result = _build_hadith_result(
                    hadith=hadith,
                    book=book,
                    collection=collection,
                    translation=translation,
                    source=source,
                    translation_source=translation_source,
                    query=query,
                    retrieval_score=1.0,
                )

                results.append(result)

        else:
            search_terms = expand_search_terms(
                query
            )

            english_match = expanded_english_tsquery(
                HadithTranslation.text,
                search_terms,
            )

            if english_match is not None:
                rows = (
                    db.query(
                        Hadith,
                        HadithBook,
                        HadithCollection,
                        HadithTranslation,
                        Source,
                    )
                    .join(
                        HadithBook,
                        Hadith.book_id == HadithBook.id,
                    )
                    .join(
                        HadithCollection,
                        HadithBook.collection_id
                        == HadithCollection.id,
                    )
                    .join(
                        HadithTranslation,
                        HadithTranslation.hadith_id
                        == Hadith.id,
                    )
                    .join(
                        Source,
                        HadithCollection.source_id
                        == Source.id,
                    )
                    .filter(
                        HadithTranslation.language == "en",
                        english_match,
                    )
                    .all()
                )

                for (
                    hadith,
                    book,
                    collection,
                    translation,
                    source,
                ) in rows:
                    rank_query = (
                        db.query(
                            func.ts_rank_cd(
                                func.to_tsvector(
                                    "english",
                                    translation.text,
                                ),
                                func.plainto_tsquery(
                                    "english",
                                    query,
                                ),
                            )
                        )
                        .scalar()
                    )

                    retrieval_score = float(
                        rank_query or 0.0
                    )

                    translation_source = None

                    result = _build_hadith_result(
                        hadith=hadith,
                        book=book,
                        collection=collection,
                        translation=translation,
                        source=source,
                        translation_source=translation_source,
                        query=query,
                        retrieval_score=retrieval_score,
                    )

                    results.append(result)

    # -----------------------------------------------------------------------
    # Final ranking and pagination
    # -----------------------------------------------------------------------

    results = rank_results(results)

    total = len(results)

    paginated = results[
        offset : offset + limit
    ]

    return {
        "results": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


# ---------------------------------------------------------------------------
# Evidence-set creation
# ---------------------------------------------------------------------------


@router.post(
    "/research/evidence-set",
    response_model=EvidenceSetResponse,
)
def create_research_evidence_set(
    q: str = Query(
        ...,
        min_length=1,
    ),
    domain: str = Query(
        "quran",
        pattern="^(quran|hadith)$",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    search_response = research_search(
        q=query,
        domain=domain,
        limit=100,
        offset=0,
        db=db,
    )

    selected = select_evidence_results(
        search_response["results"],
        limit,
    )

    evidence_set = EvidenceSet(
        query=query,
        domain=domain,
    )

    db.add(evidence_set)
    db.flush()

    for result in selected:
        primary_source = result.get(
            "primary_source"
        )

        source = (
            primary_source
            if primary_source is not None
            else result.get("source")
        )

        source_id = (
            source.get("id")
            if source
            else None
        )

        if source_id is None:
            continue

        item = EvidenceItem(
            evidence_set_id=evidence_set.id,
            result_type=result["result_type"],
            result_id=result["id"],
            reference=result["reference"],
            source_id=source_id,
            score=result["score"],
        )

        db.add(item)

    db.commit()
    db.refresh(evidence_set)

    return build_evidence_item_response(
        evidence_set,
        db,
    )


# ---------------------------------------------------------------------------
# Full Qur'an lookup
# ---------------------------------------------------------------------------


@router.get(
    "/research/quran/{ayah_id}",
    response_model=AyahWithTranslationsResponse,
)
def get_full_quran_ayah(
    ayah_id: int,
    db: Session = Depends(get_db),
):
    ayah = (
        db.query(Ayah)
        .filter(Ayah.id == ayah_id)
        .first()
    )

    if ayah is None:
        raise HTTPException(
            status_code=404,
            detail="Qur'an ayah not found",
        )

    surah = (
        db.query(Surah)
        .filter(Surah.id == ayah.surah_id)
        .first()
    )

    if surah is None:
        raise HTTPException(
            status_code=404,
            detail="Surah not found",
        )

    translations = (
        db.query(Translation)
        .filter(
            Translation.ayah_id == ayah.id
        )
        .all()
    )

    return {
        "id": ayah.id,
        "surah_id": ayah.surah_id,
        "surah_number": surah.number,
        "surah_name_arabic": surah.name_arabic,
        "surah_name_english": surah.name_english,
        "number": ayah.number,
        "text_arabic": ayah.text_arabic,
        "translations": [
            {
                "id": translation.id,
                "text": translation.text,
                "translator": translation.translator,
                "language": translation.language,
                "source_id": translation.source_id,
            }
            for translation in translations
        ],
    }


# ---------------------------------------------------------------------------
# Full Hadith lookup
# ---------------------------------------------------------------------------


@router.get(
    "/research/hadith/{hadith_id}",
    response_model=HadithResponse,
)
def get_full_hadith(
    hadith_id: int,
    db: Session = Depends(get_db),
):
    hadith = (
        db.query(Hadith)
        .filter(Hadith.id == hadith_id)
        .first()
    )

    if hadith is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith not found",
        )

    book = (
        db.query(HadithBook)
        .filter(HadithBook.id == hadith.book_id)
        .first()
    )

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith book not found",
        )

    collection = (
        db.query(HadithCollection)
        .filter(
            HadithCollection.id
            == book.collection_id
        )
        .first()
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Hadith collection not found",
        )

    source = (
        db.query(Source)
        .filter(
            Source.id == collection.source_id
        )
        .first()
    )

    translations = (
        db.query(HadithTranslation)
        .filter(
            HadithTranslation.hadith_id
            == hadith.id
        )
        .all()
    )

    translation_results = []

    for translation in translations:
        translation_source = (
            db.query(Source)
            .filter(
                Source.id
                == translation.source_id
            )
            .first()
        )

        translation_results.append(
            {
                "id": translation.id,
                "text": translation.text,
                "translator": translation.translator,
                "language": translation.language,
                "source": build_source_response(
                    translation_source
                ),
            }
        )

    gradings = []

    if hasattr(hadith, "gradings"):
        for grading in hadith.gradings:
            gradings.append(
                {
                    "id": grading.id,
                    "grade": grading.grade,
                    "grader": grading.grader,
                    "source_id": grading.source_id,
                }
            )

    return {
        "id": hadith.id,
        "reference": hadith.reference,
        "text_arabic": hadith.text_arabic,
        "narrator": hadith.narrator,
        "book": {
            "id": book.id,
            "number": book.number,
            "name": book.name,
        },
        "collection": {
            "id": collection.id,
            "name": collection.name,
        },
        "source": build_source_response(
            source
        ),
        "translations": translation_results,
        "gradings": gradings,
    }