"""Tests for level normalization."""
from __future__ import annotations

import unittest

from app.core.levels import normalize_level


class LevelNormalizationTests(unittest.TestCase):
    def test_normalize_level_exact(self) -> None:
        self.assertEqual(normalize_level("zakladni"), "zakladni")
        self.assertEqual(normalize_level("vysoka"), "vysoka")

    def test_normalize_level_alias(self) -> None:
        self.assertEqual(normalize_level("vs"), "vysoka")

    def test_normalize_level_numeric(self) -> None:
        self.assertEqual(normalize_level("1"), "zakladni")
        self.assertEqual(normalize_level("3"), "stredni")
        self.assertEqual(normalize_level("5"), "vysoka")

    def test_normalize_level_unknown(self) -> None:
        self.assertIsNone(normalize_level("doktorska"))


if __name__ == "__main__":
    unittest.main()
