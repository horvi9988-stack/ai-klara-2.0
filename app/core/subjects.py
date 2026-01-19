"""Subject normalization helpers."""
from __future__ import annotations

SUBJECTS: set[str] = {
    "dejepis",
    "matematika",
    "ekonomie",
    "anglictina",
    "programovani",
}

SUBJECT_ALIASES: dict[str, str] = {
    "history": "dejepis",
    "math": "matematika",
    "ekonomika": "ekonomie",
    "aj": "anglictina",
    "prog": "programovani",
}


def normalize_subject(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip().lower()
    if not cleaned:
        return None
    if cleaned in SUBJECTS:
        return cleaned
    return SUBJECT_ALIASES.get(cleaned)
