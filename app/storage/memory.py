from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


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
    preferences: dict[str, str | None] = field(default_factory=dict)


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
    }
    return StudentMemory(lesson_history=history, preferences=preferences)


def save_memory(path: Path, memory: StudentMemory) -> None:
    payload = {
        "lesson_history": [record.__dict__ for record in memory.lesson_history],
        "preferences": memory.preferences,
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


def _coerce_record(item: object) -> LessonRecord | None:
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
