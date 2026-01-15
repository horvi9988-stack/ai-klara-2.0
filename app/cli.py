from __future__ import annotations

"""CLI entrypoint for Klara AI tutoring flow (clean header)."""

from dataclasses import dataclass
from pathlib import Path

from app.core.evaluator import evaluate_answer
from app.core.levels import normalize_level
from app.core.mock_llm import reply
from app.core.question_engine import Question, generate_question
from app.core.subjects import normalize_subject
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.storage.memory import (
    add_lesson_record,
    get_topic_stats,
    get_weakest_topics,
    load_memory,
    save_memory,
    update_weakness_stats,
)


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
        memory = load_memory(context.memory_path)
        top_weakness = _format_top_weakness(memory)
        return (
            f"state={context.engine.state} "
            f"section={context.session.current_section} "
            f"strictness={context.engine.strictness} errors={context.engine.errors} "
            f"subject={context.subject or 'unset'} "
            f"level={context.level or 'unset'} "
            f"topic={context.topic or 'unset'} "
            f"weakness={top_weakness}"
        )

    if cmd == "/help":
        return "\n".join(
            [
                "/start",
                "/subject <name> (alias /s)",
                "/level <name> (alias /lvl)",
                "/topic <text>",
                "/ask",
                "/answer <text> (alias /a)",
                "/repeat",
                "/next",
                "/quiz <n>",
                "/weak",
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
        return _ask_next_question(context)

    if cmd == "/next":
        return _ask_next_question(context)

    if cmd == "/repeat":
        if context.session.last_question:
            return context.session.last_question
        return "Nejdrive poloz otazku pomoci /ask."

    if cmd.startswith("/answer ") or cmd.startswith("/a "):
        raw = cmd.replace("/answer ", "", 1).replace("/a ", "", 1).strip()
        return _handle_answer(context, raw)

    if cmd == "/weak":
        if not context.subject:
            return "Nejdrive nastav predmet pomoci /subject."
        memory = load_memory(context.memory_path)
        weakest = get_weakest_topics(memory, subject=context.subject, limit=3)
        if not weakest:
            return "Zatim nemam data o slabinach."
        lines = [
            f"{index + 1}. {topic} (fail_rate={fail_rate:.0%}, total={total})"
            for index, (topic, fail_rate, total) in enumerate(weakest)
        ]
        return "\n".join(lines)

    if cmd.startswith("/quiz"):
        parts = cmd.split(maxsplit=1)
        count = 5
        if len(parts) == 2 and parts[1].strip():
            try:
                count = max(1, int(parts[1].strip()))
            except ValueError:
                return "Pouzij: /quiz <n>"
        questions: list[Question] = []
        for _ in range(count):
            questions.append(_generate_question(context))
        if questions:
            last_question = questions[-1]
            context.session.last_question = last_question.text
            context.session.last_question_meta = last_question.meta
        context.session.questions_asked_count += count
        return "\n".join(
            f"{index + 1}. {question.text}" for index, question in enumerate(questions)
        )

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


def _ask_next_question(context: CliContext) -> str:
    question = _generate_question(context)
    context.session.last_question = question.text
    context.session.last_question_meta = question.meta
    context.session.questions_asked_count += 1
    return question.text


def _generate_question(context: CliContext) -> Question:
    memory = load_memory(context.memory_path)
    prefer_easy = _should_prefer_easy(memory, context.subject, context.topic)
    return generate_question(
        context.subject,
        context.level,
        context.topic,
        context.engine.strictness,
        prefer_easy=prefer_easy,
    )


def _handle_answer(context: CliContext, answer_text: str) -> str:
    if not context.session.last_question or not context.session.last_question_meta:
        return "Nejdrive poloz otazku pomoci /ask."
    context.session.last_answer = answer_text
    evaluation = evaluate_answer(context.session.last_question_meta, answer_text)
    context.engine.evaluate(correct=evaluation.ok)
    if evaluation.ok:
        context.session.ok_count += 1
    else:
        context.session.fail_count += 1

    memory = load_memory(context.memory_path)
    update_weakness_stats(
        memory,
        subject=context.session.last_question_meta.subject,
        topic=context.session.last_question_meta.topic,
        ok=evaluation.ok,
    )
    save_memory(context.memory_path, memory)

    return _format_feedback(context.engine.strictness, evaluation.ok, evaluation.score, evaluation.feedback_tags)


def _format_feedback(strictness: int, ok: bool, score: float, tags: list[str]) -> str:
    score_pct = f"{score:.0%}"
    if strictness <= 2:
        base = "Skvela prace." if ok else "Nevadi, zkusime to znovu."
        guidance = "Doporuceni: zkus pripsat konkretni fakta." if not ok else "Doporuceni: muzes jit na dalsi otazku."
        return f"{base} Skore {score_pct}. {guidance}"
    if strictness == 3:
        base = "Odpoved je spravna." if ok else "Odpoved neni dostatecna."
        guidance = "Doporuceni: zamer se na klicova slova." if not ok else "Doporuceni: pokracuj dal."
        return f"{base} Skore {score_pct}. {guidance}"
    base = "OK." if ok else "Spatne."
    guidance = "Krok 1: oprav odpoved. Krok 2: zkus /next." if not ok else "Krok 1: jdi na /next."
    tag_info = f" ({', '.join(tags)})" if tags else ""
    return f"{base} Skore {score_pct}.{tag_info} {guidance}"


def _should_prefer_easy(memory, subject: str | None, topic: str | None) -> bool:
    if not subject or not topic:
        return False
    stats = get_topic_stats(memory, subject=subject, topic=topic)
    if not stats:
        return False
    total = stats.get("total", 0)
    fail = stats.get("fail", 0)
    if total < 5:
        return False
    fail_rate = fail / total if total else 0
    return fail_rate > 0.6


def _format_top_weakness(memory) -> str:
    weakest_overall: tuple[str, str, float, int] | None = None
    for subject, topics in memory.weakness_stats.items():
        if not isinstance(topics, dict):
            continue
        for topic, stats in topics.items():
            if not isinstance(stats, dict):
                continue
            total = stats.get("total", 0)
            fail = stats.get("fail", 0)
            if not isinstance(total, int) or total <= 0:
                continue
            fail_rate = fail / total
            if not weakest_overall or fail_rate > weakest_overall[2]:
                weakest_overall = (subject, topic, fail_rate, total)
    if not weakest_overall:
        return "none"
    subject, topic, fail_rate, total = weakest_overall
    return f"{subject}:{topic} ({fail_rate:.0%}, total={total})"


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
