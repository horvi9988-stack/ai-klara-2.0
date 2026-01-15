from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.mock_llm import reply
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.storage.memory import add_lesson_record, load_memory, save_memory


APP_DIR = Path(__file__).resolve().parent
PROMPT_PATH = APP_DIR / "prompts" / "klara.txt"
MEMORY_PATH = APP_DIR / "storage" / "student_memory.json"


@dataclass
class CliContext:
    engine: TeacherEngine
    session: LessonSession
    memory_path: Path
    persona_text: str
    topic: str | None = None


def handle_command(context: CliContext, command: str) -> str:
    cmd = command.strip()
    if cmd == "/help":
        return (
            "Prikazy: /help /start /topic <text> /status /ok /fail /end"
        )
    if cmd == "/start":
        context.engine.start_lesson()
        context.session.reset()
        return _respond(context, context.session.current_section, "")
    if cmd == "/status":
        return (
            f"section={context.session.current_section} "
            f"strictness={context.engine.strictness} errors={context.engine.errors} "
            f"strictness_peak={context.engine.strictness_peak} "
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
        section_reached = context.session.current_section
        message = context.engine.end_lesson()

        memory = load_memory(context.memory_path)
        add_lesson_record(
            memory,
            errors=errors,
            strictness_peak=strictness_peak,
            topic=context.topic,
            section_reached=section_reached,
        )
        save_memory(context.memory_path, memory)

        context.session.reset()
        return message

    if cmd.startswith("/topic"):
        parts = cmd.split(maxsplit=1)
        context.topic = parts[1].strip() if len(parts) > 1 else None
        if context.topic == "":
            context.topic = None

        memory = load_memory(context.memory_path)
        memory.preferences["topic"] = context.topic
        save_memory(context.memory_path, memory)

        return "Tema nastavene."

    return "Neznamy prikaz. Pouzij /help."


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
    if not MEMORY_PATH.parent.exists():
        MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    memory = load_memory(MEMORY_PATH)
    context = CliContext(
        engine=TeacherEngine(),
        session=LessonSession(),
        memory_path=MEMORY_PATH,
        persona_text=persona_text,
        topic=memory.preferences.get("topic"),
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
