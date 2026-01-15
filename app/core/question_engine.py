from __future__ import annotations

import random


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
    "Soustreď se. Pracuj presne.",
    "Bez odbihani. Jdi primo k veci.",
    "Disciplina. Strucna odpoved.",
]

SUBJECT_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "dejepis": {
        "zakladni": [
            "Vysvetli jednou vetou, co se stalo v {topic}.",
            "Kdo byl hlavni aktér {topic}?",
            "Jaky byl nejdulezitejsi dusledek {topic}?",
        ],
        "stredni": [
            "Porovnej 2 priciny {topic}.",
            "Jak {topic} ovlivnilo Evropu?",
            "Uved 2 klicove udalosti v ramci {topic}.",
        ],
        "vysoka": [
            "Analyzuj pricinny retezec udalosti v {topic}.",
            "Jak bys obhajil vyznam {topic} v dlouhem obdobi?",
            "Srovnej interpretace {topic} z pohledu dvou skol.",
        ],
    },
    "matematika": {
        "zakladni": [
            "Vypocitej priklad k tematu {topic}.",
            "Uved jednoduche pravidlo pro {topic}.",
            "Spocitej kratky priklad na {topic}.",
        ],
        "stredni": [
            "Vyres ulohu stredni obtiznosti na {topic}.",
            "Popis postup reseni pro {topic}.",
            "Uved vzorec a aplikuj ho na {topic}.",
        ],
        "vysoka": [
            "Odvod rovnice souvisejici s {topic}.",
            "Vysvetli dukaz tvrzeni pro {topic}.",
            "Aplikuj pokrocily postup na {topic}.",
        ],
    },
    "ekonomie": {
        "zakladni": [
            "Definuj pojem souvisejici s {topic}.",
            "Uved priklad z praxe k {topic}.",
            "Co je nejdulezitejsi myslenka u {topic}?",
        ],
        "stredni": [
            "Popis mechanismus {topic} a jeho dopady.",
            "Jak {topic} ovlivnuje trh?",
            "Uved 2 faktory, ktere meni {topic}.",
        ],
        "vysoka": [
            "Zhodnot dopady {topic} na makroekonomii.",
            "Srovnej dva pristupy k {topic}.",
            "Navrhni policy doporuceni pro {topic}.",
        ],
    },
}

DEFAULT_TEMPLATES = {
    "zakladni": ["Vysvetli zakladni pojem souvisejici s {topic}."],
    "stredni": ["Popis souvislosti u tematu {topic}."],
    "vysoka": ["Analyzuj tema {topic} do hloubky."],
}


def generate_question(
    subject: str | None,
    level: str | None,
    topic: str | None,
    strictness: int,
) -> str:
    normalized_subject = subject or "obecne"
    normalized_level = _normalize_level(level)
    topic_text = topic.strip() if topic else "tematu"
    templates = SUBJECT_TEMPLATES.get(normalized_subject, DEFAULT_TEMPLATES)
    choices = templates.get(normalized_level, DEFAULT_TEMPLATES[normalized_level])
    question = random.choice(choices).format(topic=topic_text)

    if strictness <= 2:
        tone = random.choice(SUPPORTIVE_TONES)
        return f"{tone} {question}"
    if strictness == 3:
        tone = random.choice(NEUTRAL_TONES)
        return f"{tone} Otazka: {question}"
    tone = random.choice(STRICT_TONES)
    step_1 = "Krok 1: Ujasni si pojmy."
    step_2 = f"Krok 2: Zamer se na {topic_text}."
    return f"{tone} {step_1} {step_2} Otazka: {question}"


def _normalize_level(level: str | None) -> str:
    if level in {"zakladni", "stredni", "vysoka"}:
        return level
    return "zakladni"
