from __future__ import annotations

"""Tests for question generation."""

import unittest

from app.core.local_sources import SourceChunk
from app.core.question_engine import generate_question


class QuestionEngineTests(unittest.TestCase):
    def test_generate_question_contains_topic(self) -> None:
        question = generate_question("dejepis", "stredni", "1. svetova valka", 3)
        self.assertIsInstance(question.text, str)
        self.assertIn("1. svetova valka", question.text)
        self.assertEqual(question.meta.topic, "1. svetova valka")

    def test_generate_question_includes_citation(self) -> None:
        sources = [
            SourceChunk(
                id="ekon-p12-1",
                source_file="EKONOMIE_STUDIJNI_OPORA_2025.pdf",
                page_num=12,
                text="Inflace je trvaly rust cenove hladiny.",
            )
        ]
        question = generate_question("ekonomie", "zakladni", "inflace", 2, sources=sources)
        self.assertIn("[Source: EKONOMIE_STUDIJNI_OPORA_2025.pdf p.12]", question.text)


if __name__ == "__main__":
    unittest.main()
