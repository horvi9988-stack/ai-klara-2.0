import unittest

from app.core.question_engine import QuestionMeta, TYPE_FACT
from app.core.session import LessonSession


class SessionTests(unittest.TestCase):
    def test_session_stores_last_question_and_answer(self) -> None:
        session = LessonSession()
        meta = QuestionMeta(
            subject="dejepis",
            level="zakladni",
            topic="stredovek",
            template_id="hist_basic_1",
            expected_keywords=["stredovek"],
            difficulty_tag="easy",
            question_type=TYPE_FACT,
        )
        session.last_question = "Kdo byl Karel IV?"
        session.last_question_meta = meta
        session.last_answer = "Byl to cesky kral."
        self.assertEqual(session.last_question, "Kdo byl Karel IV?")
        self.assertEqual(session.last_question_meta.topic, "stredovek")
        self.assertEqual(session.last_answer, "Byl to cesky kral.")


if __name__ == "__main__":
    unittest.main()
