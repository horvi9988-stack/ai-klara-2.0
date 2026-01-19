import unittest

from app.core.evaluator import evaluate_answer
from app.core.question_engine import QuestionMeta, TYPE_EXPLAIN


class EvaluatorTests(unittest.TestCase):
    def test_keyword_scoring_ok(self) -> None:
        meta = QuestionMeta(
            subject="dejepis",
            level="stredni",
            topic="1. svetova valka",
            template_id="hist_mid_1",
            expected_keywords=["1. svetova valka", "pricina"],
            difficulty_tag="medium",
            question_type=TYPE_EXPLAIN,
        )
        result = evaluate_answer(meta, "Byla to pricina i dopad 1. svetova valka.")
        self.assertTrue(result.ok)

    def test_hard_keyword_requirement_caps_at_keyword_count(self) -> None:
        meta = QuestionMeta(
            subject="matematika",
            level="vysoka",
            topic="integral",
            template_id="math_high_1",
            expected_keywords=["integral", "odvod"],
            difficulty_tag="hard",
            question_type=TYPE_EXPLAIN,
        )
        result = evaluate_answer(meta, "integral a odvod jsem popsal")
        self.assertTrue(result.ok)

if __name__ == "__main__":
    unittest.main()
