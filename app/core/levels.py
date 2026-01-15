from __future__ import annotations

LEVELS = {
    "zakladni",
    "stredni",
    "vysoka",
    "maturita",
    "bakalarska",
    "magisterska",
}

LEVEL_ALIASES = {
    "zs": "zakladni",
    "ss": "stredni",
    "vs": "vysoka",
    "bachelor": "bakalarska",
    "master": "magisterska",
}

LEVEL_NUMERIC_MAP = {
    "1": "zakladni",
    "2": "zakladni",
    "3": "stredni",
    "4": "vysoka",
    "5": "vysoka",
}


def normalize_level(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip().lower()
    if not cleaned:
        return None
    if cleaned in LEVELS:
        return cleaned
    if cleaned in LEVEL_NUMERIC_MAP:
        return LEVEL_NUMERIC_MAP[cleaned]
    return LEVEL_ALIASES.get(cleaned)
