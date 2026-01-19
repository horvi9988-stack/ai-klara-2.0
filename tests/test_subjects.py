"""Tests for subject normalization."""
from __future__ import annotations

import unittest

from app.core.subjects import normalize_subject


class SubjectNormalizationTests(unittest.TestCase):
    def test_normalize_subject_exact(self) -> None:
        self.assertEqual(normalize_subject("dejepis"), "dejepis")
        self.assertEqual(normalize_subject("matematika"), "matematika")

    def test_normalize_subject_alias(self) -> None:
        self.assertEqual(normalize_subject("aj"), "anglictina")

    def test_normalize_subject_unknown(self) -> None:
        self.assertIsNone(normalize_subject("biology"))


if __name__ == "__main__":
    unittest.main()
