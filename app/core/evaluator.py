from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.question_engine import QuestionMeta, TYPE_MATH


@dataclass
class EvaluationResult:
    ok: bool
    score: float
    feedback_tags: list[str]


def evaluate_answer(question_meta: QuestionMeta, answer_text: str) -> EvaluationResult:
    cleaned_answer = answer_text.strip().lower()
    if not cleaned_answer:
        return EvaluationResult(ok=False, score=0.0, feedback_tags=["empty_answer"])

    if question_meta.question_type == TYPE_MATH and question_meta.expected_answer is not None:
        numeric = _extract_number(cleaned_answer)
        if numeric is None:
            return EvaluationResult(ok=False, score=0.0, feedback_tags=["missing_number"])
        ok = numeric == question_meta.expected_answer
        return EvaluationResult(ok=ok, score=1.0 if ok else 0.0, feedback_tags=["math_check"])

    keywords = [keyword.lower() for keyword in question_meta.expected_keywords if keyword]
    if not keywords:
        return EvaluationResult(ok=True, score=1.0, feedback_tags=["no_keywords"])

    matched = [keyword for keyword in keywords if keyword in cleaned_answer]
    required = _required_keyword_count(question_meta.difficulty_tag)
    score = len(matched) / len(keywords)
    ok = len(matched) >= required
    feedback_tags = ["keyword_scoring"]
    if matched:
        feedback_tags.append("keywords_matched")
    if len(matched) < required:
        feedback_tags.append("missing_keywords")
    return EvaluationResult(ok=ok, score=score, feedback_tags=feedback_tags)


def _extract_number(text: str) -> float | None:
    match = re.search(r"-?\d+(?:[\.,]\d+)?", text)
    if not match:
        return None
    raw = match.group(0).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _required_keyword_count(difficulty_tag: str) -> int:
    if difficulty_tag == "easy":
        return 1
    if difficulty_tag == "medium":
        return 2
    return 3
