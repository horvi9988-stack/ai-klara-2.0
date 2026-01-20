"""Persistent student memory storage."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LessonRecord:
    timestamp: str
    errors: int
    strictness_peak: int
    topic: str | None = None
    subject: str | None = None
    level: str | None = None
    questions_asked_count: int = 0
    section_reached: str | None = None


@dataclass
class StudentMemory:
    lesson_history: list[LessonRecord] = field(default_factory=list)
    preferences: dict[str, object] = field(default_factory=dict)
    weakness_stats: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)


def load_memory(path: Path) -> StudentMemory:
    if not path.exists():
        return StudentMemory()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return StudentMemory()
    history_data = data.get("lesson_history", [])
    history: list[LessonRecord] = []
    if isinstance(history_data, list):
        for item in history_data:
            record = _coerce_record(item)
            if record:
                history.append(record)
    preferences = data.get("preferences", {})
    if not isinstance(preferences, dict):
        preferences = {}
    preferences = {
        "subject": preferences.get("subject"),
        "level": preferences.get("level"),
        "topic": preferences.get("topic"),
<<<<<<< ours
        "teacher": preferences.get("teacher"),
=======
        "llm_enabled": preferences.get("llm_enabled"),
        "llm_model": preferences.get("llm_model"),
        "voice_enabled": preferences.get("voice_enabled"),
>>>>>>> theirs
    }
    weakness_stats = data.get("weakness_stats", {})
    if not isinstance(weakness_stats, dict):
        weakness_stats = {}
    return StudentMemory(lesson_history=history, preferences=preferences, weakness_stats=weakness_stats)


def save_memory(path: Path, memory: StudentMemory) -> None:
    payload = {
        "lesson_history": [record.__dict__ for record in memory.lesson_history],
        "preferences": memory.preferences,
        "weakness_stats": memory.weakness_stats,
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def add_lesson_record(
    memory: StudentMemory,
    *,
    errors: int,
    strictness_peak: int,
    topic: str | None = None,
    subject: str | None = None,
    level: str | None = None,
    questions_asked_count: int = 0,
    section_reached: str | None = None,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    memory.lesson_history.append(
        LessonRecord(
            timestamp=timestamp,
            errors=errors,
            strictness_peak=strictness_peak,
            topic=topic,
            subject=subject,
            level=level,
            questions_asked_count=questions_asked_count,
            section_reached=section_reached,
        )
    )


def update_weakness_stats(
    memory: StudentMemory,
    *,
    subject: str,
    topic: str,
    ok: bool,
) -> None:
    subject_stats = memory.weakness_stats.setdefault(subject, {})
    topic_stats = subject_stats.setdefault(topic, {"total": 0, "ok": 0, "fail": 0})
    topic_stats["total"] += 1
    if ok:
        topic_stats["ok"] += 1
    else:
        topic_stats["fail"] += 1


def get_topic_stats(
    memory: StudentMemory,
    *,
    subject: str,
    topic: str,
) -> dict[str, int] | None:
    subject_stats = memory.weakness_stats.get(subject, {})
    if not isinstance(subject_stats, dict):
        return None
    topic_stats = subject_stats.get(topic)
    if not isinstance(topic_stats, dict):
        return None
    return topic_stats


def get_weakest_topics(memory: StudentMemory, *, subject: str, limit: int) -> list[tuple[str, float, int]]:
    subject_stats = memory.weakness_stats.get(subject, {})
    if not isinstance(subject_stats, dict):
        return []
    scored: list[tuple[str, float, int]] = []
    for topic, stats in subject_stats.items():
        if not isinstance(stats, dict):
            continue
        total = stats.get("total", 0)
        fail = stats.get("fail", 0)
        if not isinstance(total, int) or not isinstance(fail, int) or total <= 0:
            continue
        fail_rate = fail / total
        scored.append((topic, fail_rate, total))
    scored.sort(key=lambda item: (item[1], item[2]), reverse=True)
    return scored[:limit]


def _coerce_record(item: Any) -> LessonRecord | None:
    if not isinstance(item, dict):
        return None
    timestamp = item.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()
    errors = item.get("errors", 0)
    strictness_peak = item.get("strictness_peak", 1)
    topic = item.get("topic")
    subject = item.get("subject")
    level = item.get("level")
    questions_asked_count = item.get("questions_asked_count", 0)
    section_reached = item.get("section_reached")
    return LessonRecord(
        timestamp=timestamp,
        errors=errors if isinstance(errors, int) else 0,
        strictness_peak=strictness_peak if isinstance(strictness_peak, int) else 1,
        topic=topic if isinstance(topic, str) or topic is None else None,
        subject=subject if isinstance(subject, str) or subject is None else None,
        level=level if isinstance(level, str) or level is None else None,
        questions_asked_count=questions_asked_count if isinstance(questions_asked_count, int) else 0,
        section_reached=section_reached if isinstance(section_reached, str) or section_reached is None else None,
    )
