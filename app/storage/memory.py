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
    section_reached: str | None = None


@dataclass
class StudentMemory:
    lesson_history: list[LessonRecord] = field(default_factory=list)
    preferences: dict[str, str | None] = field(default_factory=dict)


def load_memory(path: Path) -> StudentMemory:
    if not path.exists():
        return StudentMemory()
    data = json.loads(path.read_text(encoding="utf-8"))
    history = [LessonRecord(**item) for item in data.get("lesson_history", [])]
    preferences = data.get("preferences", {})
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
    section_reached: str | None = None,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    memory.lesson_history.append(
        LessonRecord(
            timestamp=timestamp,
            errors=errors,
            strictness_peak=strictness_peak,
            topic=topic,
            section_reached=section_reached,
        )
    )
