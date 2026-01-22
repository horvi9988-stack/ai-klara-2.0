from __future__ import annotations

"""LLM-backed question generation."""

from app.core.local_sources import SourceChunk, retrieve_chunks
from app.core.question_engine import Question, QuestionMeta, TYPE_EXPLAIN
from app.llm.ollama_client import generate


def generate_llm_question(
    subject: str | None,
    level: str | None,
    topic: str | None,
    strictness: int,
    *,
    sources: list[SourceChunk],
    model: str,
    preview_len: int = 300,
) -> Question | None:
    subject_label = subject or "obecne"
    level_label = level or "zakladni"
    topic_text = topic.strip() if topic else "tematu"
    retrieved = retrieve_chunks(sources, f"{subject_label} {topic_text} {level_label}", limit=3)
    prompt = _build_prompt(subject_label, level_label, topic_text, strictness, retrieved)
    response = generate(prompt, model=model)
    cleaned = _extract_question(response)
    if not cleaned or _looks_unavailable(response):
        return None
    cleaned = _attach_document_preview(cleaned, retrieved, preview_len)
    meta = QuestionMeta(
        subject=subject_label,
        level=level_label,
        topic=topic_text,
        template_id="llm",
        expected_keywords=[],
        difficulty_tag="adaptive",
        question_type=TYPE_EXPLAIN,
        expected_answer=None,
    )
    return Question(text=cleaned, meta=meta)


def _build_prompt(
    subject: str,
    level: str,
    topic: str,
    strictness: int,
    sources: list[SourceChunk],
) -> str:
    header = (
        "You are a tutoring assistant.\n"
        "Create one short question in Czech without diacritics.\n"
        "Use the subject, level, and topic.\n"
        "Return only the question text, no bullets, no numbering.\n"
        f"Subject: {subject}\n"
        f"Level: {level}\n"
        f"Topic: {topic}\n"
        f"Strictness: {strictness}\n"
    )
    if not sources:
        return header
    source_lines = "\n".join(
        f"- {chunk.text[:300]}" for chunk in sources if chunk.text.strip()
    )
    return f"{header}Sources:\n{source_lines}"


def _extract_question(text: str) -> str:
    cleaned = text.strip().splitlines()[0] if text.strip() else ""
    cleaned = cleaned.lstrip("-*0123456789. ").strip()
    if cleaned and not cleaned.endswith("?"):
        cleaned = f"{cleaned}?"
    return cleaned


def _looks_unavailable(text: str) -> bool:
    lowered = text.lower()
    return (
        "ollama is not running" in lowered
        or "ollama returned an empty response" in lowered
        or "ollama request timed out" in lowered
        or lowered.startswith("ollama error")
    )


def _attach_document_preview(
    question: str,
    retrieved: list[SourceChunk],
    preview_len: int,
) -> str:
    if not retrieved:
        return question
    chunk = retrieved[0]
    preview = _clip_text(chunk.text, preview_len)
    if not preview:
        return question
    citation = _format_citation(chunk)
    return f"{question}\n[From document: {preview}]\n{citation}"


def _format_citation(chunk: SourceChunk) -> str:
    return f"[Source: {chunk.source_file} p.{chunk.page_num}]"


def _clip_text(text: str, limit: int) -> str:
    cleaned = text.replace("\n", " ").strip()
    if limit <= 0:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."
