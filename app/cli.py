from __future__ import annotations

from pathlib import Path

from app.core.mock_llm import reply
from app.core.state_machine import TeacherEngine
from app.storage.memory import StudentMemory


PROMPT_PATH = Path("app/prompts/klara.txt")
MEMORY_PATH = Path("app/storage/student_memory.json")


def _load_persona() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "I am Klara, your Czech teacher."


def _print_help() -> None:
    print("Commands:")
    print("  /help                Show this help message")
    print("  /start               Start a lesson")
    print("  /status              Show current status")
    print("  /topic <text>        Set the lesson topic")
    print("  /ok                  Mark the last answer correct")
    print("  /fail                Mark the last answer incorrect")
    print("  /end                 End the lesson")


def _status_line(engine: TeacherEngine, topic: str) -> str:
    return (
        "Status | "
        f"section={engine.state.value} "
        f"strictness={engine.strictness} "
        f"errors={engine.errors} "
        f"strictness_peak={engine.strictness_peak} "
        f"topic={topic or 'unset'}"
    )


def run_cli() -> None:
    persona = _load_persona()
    engine = TeacherEngine()
    memory = StudentMemory(MEMORY_PATH)
    memory.load()
    topic = ""

    print("Type /start to begin.")
    print("Type /help to see commands.")

    while True:
        try:
            user_input = input("> ").strip()
        except EOFError:
            print()
            break

        if not user_input:
            continue

        if user_input == "/help":
            _print_help()
            continue

        if user_input.startswith("/topic"):
            parts = user_input.split(maxsplit=1)
            topic = parts[1].strip() if len(parts) > 1 else ""
            print(f"Topic set to: {topic or 'unset'}")
            continue

        if user_input == "/status":
            print(_status_line(engine, topic))
            continue

        if user_input == "/start":
            engine.start_lesson()
            response = reply(persona, engine.strictness, engine.state, topic)
            print(response)
            continue

        if user_input == "/ok":
            engine.evaluate(correct=True)
            response = reply(persona, engine.strictness, engine.state, topic)
            print(response)
            continue

        if user_input == "/fail":
            engine.evaluate(correct=False)
            response = reply(persona, engine.strictness, engine.state, topic)
            print(response)
            continue

        if user_input == "/end":
            section_reached = engine.state.value
            memory.add_lesson(
                errors=engine.errors,
                strictness_peak=engine.strictness_peak,
                topic=topic,
                section_reached=section_reached,
            )
            memory.save()
            print("Zvladli jsme to spolu.")
            engine.end_lesson()
            engine.reset()
            continue

        print("Unknown command. Type /help for a list of commands.")


if __name__ == "__main__":
    run_cli()
