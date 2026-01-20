from __future__ import annotations

"""Tests for subject normalization."""

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

    def test_normalize_subject_custom(self) -> None:
        self.assertEqual(normalize_subject("biologie", extra_subjects={"biologie"}), "biologie")


if __name__ == "__main__":
    unittest.main()
