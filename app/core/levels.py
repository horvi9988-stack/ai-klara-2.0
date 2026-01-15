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


def normalize_level(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip().lower()
    if not cleaned:
        return None
    if cleaned in LEVELS:
        return cleaned
    return LEVEL_ALIASES.get(cleaned)
