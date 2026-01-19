from __future__ import annotations

from dataclasses import dataclass

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
    section: str | None,
    strictness: int,
    *,
    prefer_easy: bool = False,
    persona_text: str = "",
    strict_mode_style: str = "",
) -> Question:
    normalized_subject = subject or "obecne"
    normalized_level = _normalize_level(level)
    topic_text = topic.strip() if topic else "tematu"
    section_label = section or "INTRO"
    templates = SUBJECT_TEMPLATES.get(normalized_subject, DEFAULT_TEMPLATES)
    choices = templates.get(normalized_level, DEFAULT_TEMPLATES[normalized_level])

    choices = _apply_section_focus(choices, section_label)
    if prefer_easy:
        easy_choices = [template for template in choices if template.get("difficulty") == "easy"]
        if easy_choices:
            choices = easy_choices
    selected = _stable_choice(
        choices,
        seed_parts=[
            normalized_subject,
            normalized_level,
            topic_text,
            section_label,
            str(strictness),
            persona_text,
        ],
    )

    text = str(selected["text"]).format(topic=topic_text)
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

    teacher_style = _teacher_style(strictness, persona_text, strict_mode_style)
    if strictness <= 2:
        tone = _stable_tone(SUPPORTIVE_TONES, topic_text, section_label, strictness)
        return Question(text=_join_parts([tone, teacher_style, text]), meta=meta)
    if strictness == 3:
        tone = _stable_tone(NEUTRAL_TONES, topic_text, section_label, strictness)
        return Question(text=_join_parts([tone, teacher_style, f"Otazka: {text}"]), meta=meta)
    tone = _stable_tone(STRICT_TONES, topic_text, section_label, strictness)
    step_1 = "Krok 1: Ujasni si pojmy."
    step_2 = f"Krok 2: Zamer se na {topic_text}."
    return Question(
        text=_join_parts([tone, teacher_style, step_1, step_2, f"Otazka: {text}"]),
        meta=meta,
    )


def _normalize_level(level: str | None) -> str:
    if level in {"zakladni", "stredni", "vysoka"}:
        return level
    return "zakladni"


def _coerce_expected_answer(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _apply_section_focus(choices: list[Template], section: str) -> list[Template]:
    section_key = section.upper()
    filtered = choices
    if section_key == "INTRO":
        filtered = _filter_by_difficulty(choices, "easy")
    elif section_key == "EXPLAIN":
        filtered = _filter_by_type(choices, {TYPE_EXPLAIN, TYPE_FACT})
    elif section_key == "PRACTICE":
        filtered = _filter_by_difficulty(choices, "medium")
    elif section_key == "TEST":
        filtered = _filter_by_difficulty(choices, "hard")
        if not filtered:
            filtered = _filter_by_type(choices, {TYPE_ANALYZE, TYPE_MATH})
    elif section_key == "RECAP":
        filtered = _filter_by_type(choices, {TYPE_FACT, TYPE_EXPLAIN})
    elif section_key == "END":
        filtered = _filter_by_difficulty(choices, "easy")
    return filtered or choices


def _filter_by_difficulty(choices: list[Template], difficulty: str) -> list[Template]:
    return [template for template in choices if template.get("difficulty") == difficulty]


def _filter_by_type(choices: list[Template], allowed_types: set[str]) -> list[Template]:
    return [template for template in choices if template.get("type") in allowed_types]


def _stable_choice(choices: list[Template], *, seed_parts: list[str]) -> Template:
    index = _stable_index("|".join(seed_parts), len(choices))
    return choices[index]


def _stable_tone(tones: list[str], topic: str, section: str, strictness: int) -> str:
    seed = f"{topic}|{section}|{strictness}"
    index = _stable_index(seed, len(tones))
    return tones[index]


def _stable_index(seed: str, length: int) -> int:
    if length <= 1:
        return 0
    total = sum(ord(char) for char in seed)
    return total % length


def _teacher_style(strictness: int, persona_text: str, strict_mode_style: str) -> str:
    if strictness >= 4 and strict_mode_style.strip():
        return strict_mode_style.strip()
    return persona_text.strip()


def _join_parts(parts: list[str]) -> str:
    return " ".join(part for part in parts if part)
