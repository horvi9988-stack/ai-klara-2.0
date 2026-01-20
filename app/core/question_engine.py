from __future__ import annotations

"""Question templates and generation logic."""

import random
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from app.core.local_sources import SourceChunk

SUPPORTIVE_TONES = [
    "Zkusme to spolu v klidu.",
    "Jde ti to skvele, pokracujeme.",
    "Neboj, zvladnes to.",
]

NEUTRAL_TONES = [
    "Odpovez vecne a strukturovane.",
    "Zamer se na jasnou odpoved.",
    "Postupuj krok za krokem.",
]

STRICT_TONES = [
    "Soustred se. Pracuj presne.",
    "Bez odbihani. Jdi primo k veci.",
    "Disciplina. Strucna odpoved.",
]

TYPE_FACT = "TYPE_FACT"
TYPE_EXPLAIN = "TYPE_EXPLAIN"
TYPE_ANALYZE = "TYPE_ANALYZE"
TYPE_MATH = "TYPE_MATH"


@dataclass
class QuestionMeta:
    subject: str
    level: str
    topic: str
    template_id: str
    expected_keywords: list[str]
    difficulty_tag: str
    question_type: str
    expected_answer: float | None = None


@dataclass
class Question:
    text: str
    meta: QuestionMeta


Template = dict[str, object]


SUBJECT_TEMPLATES: dict[str, dict[str, list[Template]]] = {
    "dejepis": {
        "zakladni": [
            {
                "id": "hist_basic_1",
                "text": "Vysvetli jednou vetou, co se stalo v {topic}.",
                "keywords": ["{topic}", "udalost"],
                "difficulty": "easy",
                "type": TYPE_FACT,
            },
            {
                "id": "hist_basic_2",
                "text": "Kdo byl hlavni aktér {topic}?",
                "keywords": ["{topic}", "kdo"],
                "difficulty": "easy",
                "type": TYPE_FACT,
            },
        ],
        "stredni": [
            {
                "id": "hist_mid_1",
                "text": "Porovnej 2 priciny {topic}.",
                "keywords": ["{topic}", "pricina", "porovnej"],
                "difficulty": "medium",
                "type": TYPE_EXPLAIN,
            },
            {
                "id": "hist_mid_2",
                "text": "Jak {topic} ovlivnilo Evropu?",
                "keywords": ["{topic}", "Evropa", "dopad"],
                "difficulty": "medium",
                "type": TYPE_EXPLAIN,
            },
        ],
        "vysoka": [
            {
                "id": "hist_high_1",
                "text": "Analyzuj pricinny retezec udalosti v {topic}.",
                "keywords": ["{topic}", "analyza", "priciny"],
                "difficulty": "hard",
                "type": TYPE_ANALYZE,
            },
            {
                "id": "hist_high_2",
                "text": "Srovnej interpretace {topic} z pohledu dvou skol.",
                "keywords": ["{topic}", "interpretace", "skola"],
                "difficulty": "hard",
                "type": TYPE_ANALYZE,
            },
        ],
    },
    "matematika": {
        "zakladni": [
            {
                "id": "math_basic_1",
                "text": "Spocitej 12 + 7 a popis postup.",
                "keywords": ["soucet"],
                "difficulty": "easy",
                "type": TYPE_MATH,
                "expected_answer": 19,
            },
            {
                "id": "math_basic_2",
                "text": "Spocitej kratky priklad na {topic}.",
                "keywords": ["{topic}", "vypocet"],
                "difficulty": "easy",
                "type": TYPE_MATH,
            },
        ],
        "stredni": [
            {
                "id": "math_mid_1",
                "text": "Vyres rovnici 2x + 5 = 17.",
                "keywords": ["rovnice", "x"],
                "difficulty": "medium",
                "type": TYPE_MATH,
                "expected_answer": 6,
            },
            {
                "id": "math_mid_2",
                "text": "Popis postup reseni pro {topic}.",
                "keywords": ["{topic}", "postup"],
                "difficulty": "medium",
                "type": TYPE_MATH,
            },
        ],
        "vysoka": [
            {
                "id": "math_high_1",
                "text": "Odvod rovnici souvisejici s {topic}.",
                "keywords": ["{topic}", "odvod"],
                "difficulty": "hard",
                "type": TYPE_MATH,
            },
            {
                "id": "math_high_2",
                "text": "Vysvetli dukaz tvrzeni pro {topic}.",
                "keywords": ["{topic}", "dukaz"],
                "difficulty": "hard",
                "type": TYPE_MATH,
            },
        ],
    },
    "ekonomie": {
        "zakladni": [
            {
                "id": "econ_basic_1",
                "text": "Definuj pojem souvisejici s {topic}.",
                "keywords": ["{topic}", "definice"],
                "difficulty": "easy",
                "type": TYPE_EXPLAIN,
            },
            {
                "id": "econ_basic_2",
                "text": "Uved priklad z praxe k {topic}.",
                "keywords": ["{topic}", "praxe"],
                "difficulty": "easy",
                "type": TYPE_EXPLAIN,
            },
        ],
        "stredni": [
            {
                "id": "econ_mid_1",
                "text": "Popis mechanismus {topic} a jeho dopady.",
                "keywords": ["{topic}", "dopad", "mechanismus"],
                "difficulty": "medium",
                "type": TYPE_EXPLAIN,
            },
            {
                "id": "econ_mid_2",
                "text": "Jak {topic} ovlivnuje trh?",
                "keywords": ["{topic}", "trh"],
                "difficulty": "medium",
                "type": TYPE_EXPLAIN,
            },
        ],
        "vysoka": [
            {
                "id": "econ_high_1",
                "text": "Zhodnot dopady {topic} na makroekonomii.",
                "keywords": ["{topic}", "makro", "dopad"],
                "difficulty": "hard",
                "type": TYPE_ANALYZE,
            },
            {
                "id": "econ_high_2",
                "text": "Srovnej dva pristupy k {topic}.",
                "keywords": ["{topic}", "pristup", "srovnej"],
                "difficulty": "hard",
                "type": TYPE_ANALYZE,
            },
        ],
    },
}

DEFAULT_TEMPLATES = {
    "zakladni": [
        {
            "id": "default_basic",
            "text": "Vysvetli zakladni pojem souvisejici s {topic}.",
            "keywords": ["{topic}"],
            "difficulty": "easy",
            "type": TYPE_EXPLAIN,
        }
    ],
    "stredni": [
        {
            "id": "default_mid",
            "text": "Popis souvislosti u tematu {topic}.",
            "keywords": ["{topic}", "souvislost"],
            "difficulty": "medium",
            "type": TYPE_EXPLAIN,
        }
    ],
    "vysoka": [
        {
            "id": "default_high",
            "text": "Analyzuj tema {topic} do hloubky.",
            "keywords": ["{topic}", "analyza"],
            "difficulty": "hard",
            "type": TYPE_ANALYZE,
        }
    ],
}


def generate_question(
    subject: str | None,
    level: str | None,
    topic: str | None,
    strictness: int,
    *,
    prefer_easy: bool = False,
    sources: list[SourceChunk] | None = None,
) -> Question:
    normalized_subject = subject or "obecne"
    normalized_level = _normalize_level(level)
    topic_text = topic.strip() if topic else "tematu"
    
    # Get base question from templates
    templates = SUBJECT_TEMPLATES.get(normalized_subject, DEFAULT_TEMPLATES)
    choices = templates.get(normalized_level, DEFAULT_TEMPLATES[normalized_level])

    if prefer_easy:
        easy_choices = [template for template in choices if template.get("difficulty") == "easy"]
        if easy_choices:
             choices = easy_choices
    selected = random.choice(choices)

    # Build question text
    text = str(selected["text"]).format(topic=topic_text)
    
    # If sources available, retrieve relevant context and add context hint
    context_hint = ""
    if sources:
        from app.core.local_sources import retrieve_chunks
        retrieved = retrieve_chunks(sources, f"{normalized_subject} {topic_text}", limit=1)
        if retrieved:
            chunk_preview = retrieved[0].text[:100].replace("\n", " ")
            context_hint = f"\n[Z vaseho dokumentu: {chunk_preview}...]"
            text = text + context_hint
    
    keywords = [str(keyword).format(topic=topic_text) for keyword in selected.get("keywords", [])]
    meta = QuestionMeta(
        subject=normalized_subject,
        level=normalized_level,
        topic=topic_text,
        template_id=str(selected.get("id", "unknown")),
        expected_keywords=keywords,
        difficulty_tag=str(selected.get("difficulty", "easy")),
        question_type=str(selected.get("type", TYPE_EXPLAIN)),
        expected_answer=_coerce_expected_answer(selected.get("expected_answer")),
    )

    if strictness <= 2:
        tone = random.choice(SUPPORTIVE_TONES)
        return Question(text=f"{tone} {text}", meta=meta)
    if strictness == 3:
        tone = random.choice(NEUTRAL_TONES)
        return Question(text=f"{tone} Otazka: {text}", meta=meta)
    tone = random.choice(STRICT_TONES)
    step_1 = "Krok 1: Ujasni si pojmy."
    step_2 = f"Krok 2: Zamer se na {topic_text}."
    return Question(text=f"{tone} {step_1} {step_2} Otazka: {text}", meta=meta)


def _normalize_level(level: str | None) -> str:
    if level in {"zakladni", "stredni", "vysoka"}:
        return level
    return "zakladni"


def _coerce_expected_answer(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _extract_explicit_questions_from_text(text: str) -> list[str]:
    """Extract obviously formatted questions from a block of text.

    Looks for numbered lists (e.g. "1) ...", "1.") and headings like
    "Názorné otázky" followed by lines that look like questions.
    """
    questions: list[str] = []
    # numbered items like '1) ...' or '1. ...'
    for m in re.finditer(r"^\s*(?:\d+\)|\d+\.)\s*(.+)$", text, flags=re.MULTILINE):
        q = m.group(1).strip()
        if q and len(q) > 10:
            questions.append(q)

    # sections with the word 'otáz' (covers 'otázky' / 'otázka')
    for m in re.finditer(r"(?mi)(?:názorné\s+otázky|otázky|otázka)\s*[:\-]?\s*\n(.*?)\n\n", text + "\n\n"):
        block = m.group(1).strip()
        for line in block.splitlines():
            line = line.strip()
            if line and len(line) > 10:
                questions.append(line)

    # deduplicate while preserving order
    seen = set()
    out = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def _select_topics_from_sources(sources: Iterable[SourceChunk], k: int) -> list[str]:
    """Select up to `k` topic phrases from sources using simple unigram+bigram scoring.

    This is a lightweight keyphrase extractor that prefers frequent bigrams,
    falling back to frequent unigrams. Does not require external libraries.
    """
    full = "\n\n".join(chunk.text for chunk in sources)
    text = full.lower()

    # Basic tokenization
    tokens = [t for t in re.split(r"\W+", text) if t and len(t) > 2]

    stopwords = {
        "které", "který", "která", "tedy", "proto", "kterou", "kterým",
        "může", "muset", "bude", "jsou", "je", "se", "s", "v", "na",
        "do", "pro", "za", "od", "ale", "ne", "od", "tak", "co",
    }

    filtered = [t for t in tokens if t not in stopwords]

    # unigrams frequency
    uni_freq = Counter(filtered)

    # bigrams frequency (adjacent tokens)
    bigrams = []
    for a, b in zip(filtered, filtered[1:]):
        if a not in stopwords and b not in stopwords:
            bigrams.append(f"{a} {b}")
    bi_freq = Counter(bigrams)

    # Score bigrams higher to prefer phrase topics
    candidates = []
    for phrase, score in bi_freq.most_common():
        candidates.append((phrase, score * 2))
    for term, score in uni_freq.most_common():
        candidates.append((term, score))

    seen = set()
    topics: list[str] = []
    for phrase, _ in candidates:
        if phrase in seen:
            continue
        # prefer phrases with at least one alphabetic char
        if not re.search(r"[a-zěščřžýáíéúůóťň]+", phrase):
            continue
        seen.add(phrase)
        topics.append(phrase)
        if len(topics) >= k:
            break
    return topics


def generate_lesson_from_sources(
    sources: list[SourceChunk],
    subject: str | None = None,
    level: str | None = None,
    strictness: int = 4,
    *,
    n_generated: int = 8,
) -> list[str]:
    """Create a lesson: extract explicit questions from sources and generate additional ones.

    Returns a list of question texts (strings) combining extracted and generated items.
    """
    if not sources:
        return []

    # Combine all text
    full = "\n\n".join(chunk.text for chunk in sources)

    explicit = _extract_explicit_questions_from_text(full)

    # Use improved topic selection to choose candidate topics
    topics = _select_topics_from_sources(sources, max(6, n_generated * 2))

    generated = []
    used_topics = set()
    for t in topics:
        if len(generated) >= n_generated:
            break
        if t in used_topics:
            continue
        used_topics.add(t)
        q = generate_question(subject or "obecne", level or "zakladni", t, strictness, sources=sources)
        generated.append(q.text)

    # Merge explicit (from doc) first, then generated ones
    combined: list[str] = []
    for q in explicit:
        combined.append(f"[Z dokumentu] {q}")
    for q in generated:
        combined.append(f"[Vygenerováno] {q}")

    return combined
