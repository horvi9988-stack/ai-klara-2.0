import unittest

from app.core.session import LessonSection
from app.core.state_machine import TeacherEngine


class TeacherEngineTests(unittest.TestCase):
    def test_start_resets_state(self):
        engine = TeacherEngine(strictness=5, errors=3, state=LessonSection.TEST, strictness_peak=5)
        engine.start_lesson()
        self.assertEqual(engine.state, LessonSection.INTRO)
        self.assertEqual(engine.strictness, 2)
        self.assertEqual(engine.errors, 0)
        self.assertEqual(engine.strictness_peak, 2)

    def test_ok_advances_section_and_reduces_strictness(self):
        engine = TeacherEngine()
        engine.state = LessonSection.EXPLAIN
        engine.strictness = 3
        engine.evaluate(correct=True)
        self.assertEqual(engine.state, LessonSection.PRACTICE)
        self.assertEqual(engine.strictness, 2)

    def test_fail_increases_strictness_without_advancing(self):
        engine = TeacherEngine()
        engine.state = LessonSection.PRACTICE
        engine.strictness = 3
        engine.evaluate(correct=False)
        self.assertEqual(engine.state, LessonSection.PRACTICE)
        self.assertEqual(engine.strictness, 4)
        self.assertEqual(engine.errors, 1)
        self.assertEqual(engine.strictness_peak, 4)


if __name__ == "__main__":
    unittest.main()
