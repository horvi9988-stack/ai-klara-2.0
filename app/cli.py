"""CLI entrypoint for Klara AI tutoring flow."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.evaluator import evaluate_answer
from app.core.levels import normalize_level
from app.core.mock_llm import reply
from app.core.question_engine import Question, generate_question
from app.core.subjects import normalize_subject
from app.core.teachers import (
    TeacherProfile,
    find_teacher_profile,
    get_teacher_profile,
    list_teacher_profiles,
)
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.storage.memory import (
    StudentMemory,
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
    teacher_profile: TeacherProfile
    topic: str | None = None
    subject: str | None = None
    level: str | None = None


def handle_command(context: CliContext, command: str) -> str:
    cmd, arg = _split_command(command)
    if not cmd:
        return ""

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
            f"teacher={context.teacher_profile.id}:{context.teacher_profile.name} "
            f"subject={context.subject or 'unset'} "
            f"level={context.level or 'unset'} "
            f"topic={context.topic or 'unset'} "
            f"weakness={top_weakness}"
        )

    if cmd == "/help":
        return _help_text()

    if cmd in {"/topic"}:
        if not arg:
            return "Pouzij: /topic <text>"
        context.topic = arg or None
        _persist_preference(context, "topic", context.topic)
        return f"Tema nastavene: {context.topic or 'unset'}"

    if cmd in {"/subject", "/s"}:
        if not arg:
            return "Pouzij: /subject <name>"
        subject = normalize_subject(arg)
        if not subject:
            return "Neznamy predmet."
        context.subject = subject
        _persist_preference(context, "subject", subject)
        return f"Predmet nastaven: {subject}"

    if cmd in {"/level", "/lvl"}:
        if not arg:
            return "Pouzij: /level <name>"
        level = normalize_level(arg)
        if not level:
            return "Neznama uroven."
        context.level = level
        _persist_preference(context, "level", level)
        return f"Uroven nastavena: {level}"

    if cmd == "/llm":
        if not arg:
            return "Pouzij: /llm on|off"
        value = arg.lower()
        if value not in {"on", "off"}:
            return "Pouzij: /llm on|off"
        enabled = value == "on"
        context.llm_enabled = enabled
        _persist_preference(context, "llm_enabled", enabled)
        return f"LLM mode: {'on' if enabled else 'off'}"

    if cmd == "/model":
        if not arg:
            return "Pouzij: /model <name>"
        context.llm_model = arg
        _persist_preference(context, "llm_model", arg)
        return f"Model nastaven: {arg}"

    if cmd == "/voice":
        if not arg:
            return "Pouzij: /voice on|off"
        value = arg.lower()
        if value not in {"on", "off"}:
            return "Pouzij: /voice on|off"
        if value == "off":
            context.voice_enabled = False
            _persist_preference(context, "voice_enabled", False)
            return "Voice mode: off"
        missing_messages = _missing_voice_messages()
        if missing_messages:
            return "\n".join(missing_messages)
        context.voice_enabled = True
        _persist_preference(context, "voice_enabled", True)
        return "Voice mode: on"

    if cmd == "/ptt":
        if not context.voice_enabled:
            return "Voice mode is off. Use /voice on."
        transcript, error = record_and_transcribe()
        if error:
            return error
        if transcript is None:
            return "No speech detected."
        if context.session.last_question:
            response = _handle_answer(context, transcript)
        else:
            response = _respond(context, context.session.current_section, transcript)
        speak_error = speak_text(response)
        if speak_error:
            return f"{response}\n{speak_error}"
        return response

    if cmd == "/ok":
        context.engine.evaluate(correct=True)
        section, _action = context.session.next_section()
        return _respond(context, section, "")
    if cmd == "/fail":
        context.engine.evaluate(correct=False)
        section = "STRICT_MODE" if context.engine.state == "STRICT_MODE" else context.session.current_section
        return _respond(context, section, "")

    if cmd == "/end":
        message = _end_lesson(context)
        context.session.reset()
        return message

    if cmd in {"/ask", "/next"}:
        return _ask_next_question(context)

    if cmd == "/repeat":
        if context.session.last_question:
            return context.session.last_question
        return "Nejdrive poloz otazku pomoci /ask."

    if cmd in {"/answer", "/a"}:
        if not arg:
            return "Pouzij: /answer <text>"
        return _handle_answer(context, arg)

    if cmd == "/ingest":
        if not arg:
            return "Pouzij: /ingest <path>"
        return _ingest_path(context, arg)

    if cmd == "/sources":
        if not context.sources:
            return "No sources loaded."
        return f"Sources loaded: {len(context.sources)}"

    if cmd == "/weak":
        return _weakness_report(context)

    if cmd == "/quiz":
        return _quiz_questions(context, arg)

    if not cmd.startswith("/"):
        subject = normalize_subject(cmd)
        if subject:
            context.subject = subject
            _persist_preference(context, "subject", subject)
            return f"Predmet nastaven: {subject}"
        return _respond(context, context.session.current_section, cmd)

    return "Neznamy prikaz. Pouzij /help."


def _split_command(raw: str) -> tuple[str, str]:
    cleaned = raw.strip()
    if not cleaned:
        return "", ""
    if not cleaned.startswith("/"):
        return cleaned, ""
    parts = cleaned.split(maxsplit=1)
    command = parts[0]
    argument = parts[1].strip() if len(parts) > 1 else ""
    return command, argument


def _help_text() -> str:
    return "\n".join(
        [
            "/start",
            "/subject <name> (alias /s)",
            "/level <name> (alias /lvl)",
            "/topic <text>",
            "/ingest <path>",
            "/sources",
            "/ask",
            "/answer <text> (alias /a)",
            "/repeat",
            "/next",
            "/quiz <n>",
            "/weak",
            "/llm on|off",
            "/model <name>",
            "/voice on|off",
            "/ptt",
            "/status",
            "/ok",
            "/fail",
            "/end",
        ]
    )


def _missing_voice_messages() -> list[str]:
    missing_messages = []
    voice_message = voice_dependency_message()
    if voice_message:
        missing_messages.append(voice_message)
    tts_message = tts_dependency_message()
    if tts_message:
        missing_messages.append(tts_message)
    return missing_messages


def _ingest_path(context: CliContext, raw_path: str) -> str:
    try:
        chunks = ingest_file(Path(raw_path))
    except ValueError as exc:
        return str(exc)
    if not chunks:
        return "No text found in file."
    context.sources.extend(chunks)
    return f"Ingested {len(chunks)} chunks from {raw_path}"


def _quiz_questions(context: CliContext, argument: str) -> str:
    count = 5
    if argument:
        try:
            count = max(1, int(argument))
        except ValueError:
            return "Pouzij: /quiz <n>"
    questions = [_generate_question(context) for _ in range(count)]
    if questions:
        last_question = questions[-1]
        context.session.last_question = last_question.text
        context.session.last_question_meta = last_question.meta
    context.session.questions_asked_count += count
    return "\n".join(
        f"{index + 1}. {question.text}" for index, question in enumerate(questions)
    )


def _weakness_report(context: CliContext) -> str:
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


def _respond(context: CliContext, state: str, user_text: str) -> str:
    topic_hint = context.topic or user_text
    return reply(
        context.persona_text,
        context.engine.strictness,
        state,
        topic_hint,
        subject=context.subject,
        level=context.level,
        teacher_profile=context.teacher_profile,
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
        teacher_profile=context.teacher_profile,
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


def _should_prefer_easy(memory: StudentMemory, subject: str | None, topic: str | None) -> bool:
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


def _format_top_weakness(memory: StudentMemory) -> str:
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


def _persist_preference(context: CliContext, key: str, value: object) -> None:
    memory = load_memory(context.memory_path)
    memory.preferences[key] = value
    save_memory(context.memory_path, memory)


def _end_lesson(context: CliContext) -> str:
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
    return message


def _load_preferences(memory: StudentMemory) -> dict[str, object]:
    prefs = memory.preferences if isinstance(memory.preferences, dict) else {}
    return {
        "topic": prefs.get("topic"),
        "subject": prefs.get("subject"),
        "level": prefs.get("level"),
        "llm_enabled": prefs.get("llm_enabled"),
        "llm_model": prefs.get("llm_model"),
        "voice_enabled": prefs.get("voice_enabled"),
    }


def run_cli() -> None:
    persona_text = ""
    if PROMPT_PATH.exists():
        persona_text = PROMPT_PATH.read_text(encoding="utf-8").strip()
    memory = load_memory(MEMORY_PATH)
    prefs = _load_preferences(memory)

    context = CliContext(
        engine=TeacherEngine(),
        session=LessonSession(),
        memory_path=MEMORY_PATH,
        persona_text=persona_text,
        topic=prefs["topic"] if prefs["topic"] else None,
        subject=prefs["subject"] if prefs["subject"] else None,
        level=prefs["level"] if prefs["level"] else None,
        llm_enabled=True if prefs["llm_enabled"] is True else False,
        llm_model=prefs["llm_model"] if isinstance(prefs["llm_model"], str) and prefs["llm_model"] else DEFAULT_MODEL,
        voice_enabled=True if prefs["voice_enabled"] is True else False,
    )

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
        if response:
            print(response)

        if user_input == "/end":
            break
