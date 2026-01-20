from __future__ import annotations

"""Subject normalization and sanitization helpers."""

from collections.abc import Iterable, Mapping
import re

SUBJECTS = {
    "dejepis",
    "matematika",
    "ekonomie",
    "anglictina",
    "programovani",
}

SUBJECT_ALIASES = {
    "history": "dejepis",
    "math": "matematika",
    "ekonomika": "ekonomie",
    "aj": "anglictina",
    "prog": "programovani",
}

_SUBJECT_CLEAN_RE = re.compile(r"[^\w\s-]+", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")


def normalize_subject(
    text: str | None,
    *,
    extra_subjects: Iterable[str] = (),
    extra_aliases: Mapping[str, str] | None = None,
) -> str | None:
    cleaned = _clean_text(text)
    if not cleaned:
        return None
    extra_subjects_set = {subject.strip().lower() for subject in extra_subjects if subject}
    if cleaned in SUBJECTS or cleaned in extra_subjects_set:
        return cleaned
    aliases = dict(SUBJECT_ALIASES)
    if extra_aliases:
        aliases.update({key.strip().lower(): value for key, value in extra_aliases.items() if key})
    return aliases.get(cleaned)


def sanitize_subject_name(text: str | None) -> str | None:
    cleaned = _clean_text(text)
    if not cleaned:
        return None
    cleaned = _SUBJECT_CLEAN_RE.sub("", cleaned)
    cleaned = _SPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return None
    return cleaned.replace(" ", "_")


def _clean_text(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = text.strip().lower()
    cleaned = _SPACE_RE.sub("_", cleaned)
    return cleaned or None
