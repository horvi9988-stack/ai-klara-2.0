from __future__ import annotations

"""Tests for the state machine."""

import unittest

from app.core.state_machine import MAX_STRICTNESS, MIN_STRICTNESS, TeacherEngine


class TeacherEngineTests(unittest.TestCase):
    def test_strictness_rises_on_fail(self) -> None:
        engine = TeacherEngine()
        engine.evaluate(correct=False)
        self.assertEqual(engine.strictness, MIN_STRICTNESS + 1)
        self.assertEqual(engine.errors, 1)

    def test_strictness_drops_on_ok(self) -> None:
        engine = TeacherEngine(strictness=3)
        engine.evaluate(correct=True)
        self.assertEqual(engine.strictness, 2)

    def test_reset_clears_state(self) -> None:
        engine = TeacherEngine(strictness=MAX_STRICTNESS, errors=2, strictness_peak=4)
        engine.reset()
        self.assertEqual(engine.strictness, MIN_STRICTNESS)
        self.assertEqual(engine.errors, 0)
        self.assertEqual(engine.strictness_peak, MIN_STRICTNESS)
        self.assertEqual(engine.state, "INIT")


if __name__ == "__main__":
    unittest.main()
