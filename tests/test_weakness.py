import tempfile
import unittest
from pathlib import Path

from app.storage.memory import StudentMemory, load_memory, save_memory, update_weakness_stats


class WeaknessStatsTests(unittest.TestCase):
    def test_weakness_tracking_persists(self) -> None:
        memory = StudentMemory()
        update_weakness_stats(memory, subject="dejepis", topic="1. svetova valka", ok=False)
        update_weakness_stats(memory, subject="dejepis", topic="1. svetova valka", ok=True)
        self.assertEqual(memory.weakness_stats["dejepis"]["1. svetova valka"]["total"], 2)
        self.assertEqual(memory.weakness_stats["dejepis"]["1. svetova valka"]["ok"], 1)
        self.assertEqual(memory.weakness_stats["dejepis"]["1. svetova valka"]["fail"], 1)

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            save_memory(path, memory)
            loaded = load_memory(path)
            stats = loaded.weakness_stats["dejepis"]["1. svetova valka"]
            self.assertEqual(stats["total"], 2)
            self.assertEqual(stats["ok"], 1)
            self.assertEqual(stats["fail"], 1)


if __name__ == "__main__":
    unittest.main()
