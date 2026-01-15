from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.mock_llm import reply
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.storage.memory import add_lesson_record, load_memory, save_memory


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "klara.txt"


@dataclass
class CliContext:
    engine: TeacherEngine
    session: LessonSession
    memory_path: Path
    persona_text: str
    topic: str | None = None


def handle_command(context: CliContext, command: str) -> str:
    cmd = command.strip()
    print("DEBUG_CMD:", repr(cmd))
    if cmd == "/start":
        context.engine.start_lesson()
        context.session.reset()
        return _respond(context, context.session.current_section, "")
    if cmd == "/status":
        return (
            f"state={context.engine.state} section={context.session.current_section} "
            f"strictness={context.engine.strictness} errors={context.engine.errors} "
            f"topic={context.topic or 'unset'}"
        )
    if cmd == "/ok":
        context.engine.evaluate(correct=True)
        section, _action = context.session.next_section()
        return _respond(context, section, "")
    if cmd == "/fail":
        context.engine.evaluate(correct=False)
        section = "STRICT_MODE" if context.engine.state == "STRICT_MODE" else context.session.current_section
        return _respond(context, section, "")
    if cmd == "/end":
        errors = context.engine.errors
        strictness_peak = context.engine.strictness_peak
        message = context.engine.end_lesson()

        memory = load_memory(context.memory_path)
        add_lesson_record(
            memory,
            errors=errors,
            strictness_peak=strictness_peak,
            topic=context.topic,
        )
        save_memory(context.memory_path, memory)

        context.session.reset()
        return message

    if cmd.startswith("/topic "):
        context.topic = cmd.replace("/topic ", "", 1).strip() or None

        memory = load_memory(context.memory_path)
        memory.setdefault("preferences", {})
        memory["preferences"]["topic"] = context.topic
        save_memory(context.memory_path, memory)

        return "Tema nastavene."


def _respond(context: CliContext, state: str, user_text: str) -> str:
    topic_hint = context.topic or user_text
    return reply(
        context.persona_text,
        context.engine.strictness,
        state,
        topic_hint,
    )


def run_cli() -> None:
    persona_text = ""
    if PROMPT_PATH.exists():
        persona_text = PROMPT_PATH.read_text(encoding="utf-8").strip()
    context = CliContext(
        engine=TeacherEngine(),
        session=LessonSession(),
        memory_path=Path("student_memory.json"),
        persona_text=persona_text,
    )
    print("Klara CLI. Zadej prikaz.")
    while True:
        try:
            user_input = input("> ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        response = handle_command(context, user_input)
        print(response)
        if user_input == "/end":
            break
