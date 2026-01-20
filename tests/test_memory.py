"""Tests for student memory persistence."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.storage.memory import StudentMemory, load_memory, save_memory


class MemoryPersistenceTests(unittest.TestCase):
    def test_preferences_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            memory = StudentMemory(
                preferences={
                    "subject": "dejepis",
                    "level": "vysoka",
                    "topic": "stredovek",
                    "teacher": "klara",
                }
            )
            save_memory(path, memory)
            loaded = load_memory(path)
            self.assertEqual(loaded.preferences.get("subject"), "dejepis")
            self.assertEqual(loaded.preferences.get("level"), "vysoka")
            self.assertEqual(loaded.preferences.get("topic"), "stredovek")
            self.assertEqual(loaded.preferences.get("teacher"), "klara")


if __name__ == "__main__":
    unittest.main()
