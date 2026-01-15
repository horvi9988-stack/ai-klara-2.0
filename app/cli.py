from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.levels import normalize_level
from app.core.mock_llm import reply
from app.core.question_engine import generate_question
from app.core.subjects import normalize_subject
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
    subject: str | None = None
    level: str | None = None


def handle_command(context: CliContext, command: str) -> str:
    cmd = command.strip()
    if cmd == "/start":
        context.engine.start_lesson()
        context.session.reset()
        return _respond(context, context.session.current_section, "")

    if cmd == "/status":
        return (
            f"state={context.engine.state} "
            f"section={context.session.current_section} "
            f"strictness={context.engine.strictness} errors={context.engine.errors} "
            f"subject={context.subject or 'unset'} "
            f"level={context.level or 'unset'} "
            f"topic={context.topic or 'unset'}"
        )

    if cmd == "/help":
        return "\n".join(
            [
                "/start",
                "/subject <name> (alias /s)",
                "/level <name> (alias /lvl)",
                "/topic <text>",
                "/ask",
                "/quiz <n>",
                "/status",
                "/ok",
                "/fail",
                "/end",
            ]
        )

    if cmd == "/topic":
        return "Pouzij: /topic <text>"

    if cmd.startswith("/topic "):
        context.topic = cmd.replace("/topic ", "", 1).strip() or None

        memory = load_memory(context.memory_path)
        memory.preferences["topic"] = context.topic
        save_memory(context.memory_path, memory)

        return f"Tema nastavene: {context.topic or 'unset'}"

    if cmd == "/subject":
        return "Pouzij: /subject <name>"

    if cmd.startswith("/subject ") or cmd.startswith("/s "):
        raw = cmd.replace("/subject ", "", 1).replace("/s ", "", 1).strip()
        subject = normalize_subject(raw)
        if not subject:
            return "Neznamy predmet."
        context.subject = subject
        memory = load_memory(context.memory_path)
        memory.preferences["subject"] = subject
        save_memory(context.memory_path, memory)
        return f"Predmet nastaven: {subject}"

    if cmd == "/level":
        return "Pouzij: /level <name>"

    if cmd.startswith("/level ") or cmd.startswith("/lvl "):
        raw = cmd.replace("/level ", "", 1).replace("/lvl ", "", 1).strip()
        level = normalize_level(raw)
        if not level:
            return "Neznama uroven."
        context.level = level
        memory = load_memory(context.memory_path)
        memory.preferences["level"] = level
        save_memory(context.memory_path, memory)
        return f"Uroven nastavena: {level}"

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
            subject=context.subject,
            level=context.level,
            questions_asked_count=context.session.questions_asked_count,
            section_reached=section_reached,
        )
        save_memory(context.memory_path, memory)

        context.session.reset()
        return message

    if cmd == "/ask":
        question = generate_question(
            context.subject,
            context.level,
            context.topic,
            context.engine.strictness,
        )
        context.session.questions_asked_count += 1
        return question

    if cmd.startswith("/quiz"):
        parts = cmd.split(maxsplit=1)
        count = 5
        if len(parts) == 2 and parts[1].strip():
            try:
                count = max(1, int(parts[1].strip()))
            except ValueError:
                return "Pouzij: /quiz <n>"
        questions = []
        for _ in range(count):
            questions.append(
                generate_question(
                    context.subject,
                    context.level,
                    context.topic,
                    context.engine.strictness,
                )
            )
        context.session.questions_asked_count += count
        return "\n".join(f"{index + 1}. {question}" for index, question in enumerate(questions))

    if not cmd.startswith("/"):
        subject = normalize_subject(cmd)
        if subject:
            context.subject = subject
            memory = load_memory(context.memory_path)
            memory.preferences["subject"] = subject
            save_memory(context.memory_path, memory)
            return f"Predmet nastaven: {subject}"
        return _respond(context, context.session.current_section, cmd)

    return "Neznamy prikaz. Pouzij /help."


def _respond(context: CliContext, state: str, user_text: str) -> str:
    topic_hint = context.topic or user_text
    return reply(
        context.persona_text,
        context.engine.strictness,
        state,
        topic_hint,
        subject=context.subject,
        level=context.level,
    )


def run_cli() -> None:
    persona_text = ""
    if PROMPT_PATH.exists():
        persona_text = PROMPT_PATH.read_text(encoding="utf-8").strip()
    memory = load_memory(MEMORY_PATH)
    prefs = memory.preferences if isinstance(memory.preferences, dict) else {}
    saved_topic = prefs.get("topic")
    saved_subject = prefs.get("subject")
    saved_level = prefs.get("level")
    context = CliContext(
        engine=TeacherEngine(),
        session=LessonSession(),
        memory_path=MEMORY_PATH,
        persona_text=persona_text,
        topic=saved_topic if saved_topic else None,
        subject=saved_subject if saved_subject else None,
        level=saved_level if saved_level else None,
    )

    # nacti ulozeny topic z pameti (persistuje po restartu)
    print("Klara CLI. Zadej prikaz.")
    print("Type /start")
    print("Type /help")

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
