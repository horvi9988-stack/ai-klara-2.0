import json
import os
from typing import Any, Dict


DEFAULT_MEMORY: Dict[str, Any] = {
    "preferences": {},
    "lesson_history": [],
}


class MemoryStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return _copy_default()
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return _copy_default()
        return _normalize_memory(data)

    def save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

    def set_topic(self, topic: str) -> Dict[str, Any]:
        memory = self.load()
        preferences = memory.setdefault("preferences", {})
        preferences["topic"] = topic
        self.save(memory)
        return memory


def _copy_default() -> Dict[str, Any]:
    return {
        "preferences": {},
        "lesson_history": [],
    }


def _normalize_memory(data: Dict[str, Any]) -> Dict[str, Any]:
    memory = _copy_default()
    memory.update(data)
    preferences = memory.setdefault("preferences", {})
    if not isinstance(preferences, dict):
        preferences = {}
        memory["preferences"] = preferences
    if "topic" not in preferences and "topic" in memory:
        preferences["topic"] = memory["topic"]
    if "lesson_history" not in memory or not isinstance(
        memory.get("lesson_history"), list
    ):
        memory["lesson_history"] = []
    return memory
