import json
import os
import tempfile
import unittest

from app.cli import CliApp
from app.storage.memory import MemoryStore


class TopicPersistenceTests(unittest.TestCase):
    def test_set_topic_persists_to_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "memory.json")
            memory = MemoryStore(path)
            app = CliApp(memory)

            response = app.set_topic("algebra")

            self.assertIn("algebra", response)
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["preferences"]["topic"], "algebra")

    def test_loads_topic_from_legacy_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "memory.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"topic": "geometry"}, handle)
            memory = MemoryStore(path)

            app = CliApp(memory)

            self.assertEqual(app.status(), "topic=geometry")


if __name__ == "__main__":
    unittest.main()
