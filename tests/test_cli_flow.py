import tempfile
import unittest
from pathlib import Path

from app.cli import CliContext, handle_command
from app.core.session import LessonSession
from app.core.state_machine import MIN_STRICTNESS, TeacherEngine
from app.core.teachers import DEFAULT_TEACHER_ID, get_teacher_by_id
from app.storage.memory import load_memory


def build_context(memory_path: Path) -> CliContext:
    memory = load_memory(memory_path)
    prefs = memory.preferences if isinstance(memory.preferences, dict) else {}
    teacher_id = prefs.get("teacher_id") or DEFAULT_TEACHER_ID
    teacher = get_teacher_by_id(teacher_id)
    return CliContext(
        engine=TeacherEngine(),
        session=LessonSession(),
        memory_path=memory_path,
        persona_text=teacher.persona_text,
        teacher=teacher,
    )


class CliFlowTests(unittest.TestCase):
    def test_teacher_selection_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            context = build_context(path)
            response = handle_command(context, "/teacher coach")
            self.assertIn("Focused Coach", response)
            memory = load_memory(path)
            self.assertEqual(memory.preferences.get("teacher_id"), "coach")
            new_context = build_context(path)
            self.assertEqual(new_context.teacher.id, "coach")

    def test_ok_advances_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            context = build_context(path)
            handle_command(context, "/start")
            handle_command(context, "/ok")
            self.assertEqual(context.session.current_section, "EXPLAIN")

    def test_fail_does_not_advance_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            context = build_context(path)
            handle_command(context, "/start")
            handle_command(context, "/fail")
            self.assertEqual(context.session.current_section, "INTRO")

    def test_start_resets_session_and_strictness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            context = build_context(path)
            context.engine.strictness = 4
            context.session.index = 3
            handle_command(context, "/start")
            self.assertEqual(context.session.current_section, "INTRO")
            self.assertEqual(context.engine.strictness, MIN_STRICTNESS)

    def test_end_resets_strictness_and_stores_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "memory.json"
            context = build_context(path)
            handle_command(context, "/start")
            response = handle_command(context, "/end")
            self.assertEqual(response, "Zvladli jsme to spolu.")
            self.assertEqual(context.engine.strictness, MIN_STRICTNESS)
            memory = load_memory(path)
            self.assertEqual(len(memory.lesson_history), 1)


if __name__ == "__main__":
    unittest.main()
