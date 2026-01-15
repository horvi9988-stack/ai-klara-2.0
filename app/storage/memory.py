from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StudentMemory:
    path: Path
    data: dict[str, Any] = field(default_factory=lambda: {"lesson_history": []})

    def load(self) -> None:
        if not self.path.exists():
            self.data = {"lesson_history": []}
            return
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            self.data = {"lesson_history": payload}
        elif isinstance(payload, dict):
            self.data = payload
            if "lesson_history" not in self.data:
                self.data["lesson_history"] = []
        else:
            self.data = {"lesson_history": []}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2)

    def add_lesson(self, *, errors: int, strictness_peak: int, topic: str, section_reached: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "errors": errors,
            "strictness_peak": strictness_peak,
            "topic": topic,
            "section_reached": section_reached,
        }
        history = list(self.data.get("lesson_history", []))
        history.append(entry)
        self.data["lesson_history"] = history
