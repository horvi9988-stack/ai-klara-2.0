from __future__ import annotations

"""Tests for question generation."""

import unittest

from app.core.question_engine import generate_question


class QuestionEngineTests(unittest.TestCase):
    def test_generate_question_contains_topic(self) -> None:
        question = generate_question("dejepis", "stredni", "1. svetova valka", 3)
        self.assertIsInstance(question.text, str)
        self.assertIn("1. svetova valka", question.text)
        self.assertEqual(question.meta.topic, "1. svetova valka")


if __name__ == "__main__":
    unittest.main()
