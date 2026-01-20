from __future__ import annotations

"""CLI entrypoint for Klara AI tutoring flow."""

from dataclasses import dataclass, field
from pathlib import Path

from app.core.evaluator import evaluate_answer
from app.core.llm_question_engine import generate_llm_question
from app.core.levels import normalize_level
from app.core.local_sources import build_source_chunks, ingest_file, list_sources, suggest_topic
from app.core.mock_llm import reply
from app.core.question_engine import Question, generate_question
from app.core.subjects import normalize_subject
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.core.teachers import TeacherProfile, default_teacher, get_teacher_profile, list_teachers
from app.core.voice import record_and_transcribe, speak_text, tts_dependency_message, voice_dependency_message
from app.llm.ollama_client import DEFAULT_MODEL
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
    teacher_id: str
    teacher_profile: TeacherProfile
    topic: str | None = None
    subject: str | None = None
    level: str | None = None
    llm_enabled: bool = False
    llm_model: str = DEFAULT_MODEL
    voice_enabled: bool = False
    sources: list[str] = field(default_factory=list)


def handle_command(context: CliContext, command: str) -> str:
    cmd = command.strip()
    if cmd == "/start":
        context.engine.start_lesson()
        context.session.reset()
        return _respond(context, context.session.current_section, "")

    if cmd == "/status":
        memory = load_memory(context.memory_path)
        top_weakness = _format_top_weakness(memory)
        llm_state = "on" if context.llm_enabled else "off"
        voice_state = "on" if context.voice_enabled else "off"
        return (
            f"state={context.engine.state} "
            f"section={context.session.current_section} "
            f"strictness={context.engine.strictness} errors={context.engine.errors} "
            f"subject={context.subject or 'unset'} "
            f"level={context.level or 'unset'} "
            f"topic={context.topic or 'unset'} "
            f"llm={llm_state} "
            f"model={context.llm_model} "
            f"voice={voice_state} "
            f"sources={len(context.sources)} "
            f"teacher={context.teacher_id} "
            f"weakness={top_weakness}"
        )

    if cmd == "/help":
        return "\n".join(
            [
                "/start",
                "/subject <name> (alias /s)",
                "/level <name> (alias /lvl)",
                "/topic <text>",
                "/ingest <path>",
                "/sources",
                "/teacher list",
                "/teacher set <id>",
                "/teacher show",
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

    if cmd == "/llm":
        return "Pouzij: /llm on|off"

    if cmd.startswith("/llm "):
        value = cmd.replace("/llm ", "", 1).strip().lower()
        if value not in {"on", "off"}:
            return "Pouzij: /llm on|off"
        enabled = value == "on"
        context.llm_enabled = enabled
        memory = load_memory(context.memory_path)
        memory.preferences["llm_enabled"] = enabled
        save_memory(context.memory_path, memory)
        return f"LLM mode: {'on' if enabled else 'off'}"

    if cmd == "/model":
        return "Pouzij: /model <name>"

    if cmd.startswith("/model "):
        model = cmd.replace("/model ", "", 1).strip()
        if not model:
            return "Pouzij: /model <name>"
        context.llm_model = model
        memory = load_memory(context.memory_path)
        memory.preferences["llm_model"] = model
        save_memory(context.memory_path, memory)
        return f"Model nastaven: {model}"

    if cmd == "/voice":
        return "Pouzij: /voice on|off"

    if cmd.startswith("/voice "):
        value = cmd.replace("/voice ", "", 1).strip().lower()
        if value not in {"on", "off"}:
            return "Pouzij: /voice on|off"
        if value == "off":
            context.voice_enabled = False
            memory = load_memory(context.memory_path)
            memory.preferences["voice_enabled"] = False
            save_memory(context.memory_path, memory)
            return "Voice mode: off"
        missing_messages = []
        voice_message = voice_dependency_message()
        if voice_message:
            missing_messages.append(voice_message)
        tts_message = tts_dependency_message()
        if tts_message:
            missing_messages.append(tts_message)
        if missing_messages:
            return "\n".join(missing_messages)
        context.voice_enabled = True
        memory = load_memory(context.memory_path)
        memory.preferences["voice_enabled"] = True
        save_memory(context.memory_path, memory)
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

    if cmd == "/ingest":
        return "Pouzij: /ingest <path>"

    if cmd.startswith("/ingest "):
        raw_path = cmd.replace("/ingest ", "", 1).strip()
        if not raw_path:
            return "Pouzij: /ingest <path>"
        try:
            source_id, chars_count = ingest_file(raw_path)
        except ValueError as exc:
            return str(exc)
        if chars_count <= 0:
            return "No text found in file."
        context.sources.append(source_id)
        memory = load_memory(context.memory_path)
        memory.sources.append(source_id)
        save_memory(context.memory_path, memory)
        return f"Ingested {chars_count} chars from {raw_path} as {source_id}"

    if cmd == "/sources":
        if not context.sources:
            return "No sources loaded."
        source_entries = {entry["id"]: entry for entry in list_sources()}
        lines = []
        for source_id in context.sources:
            entry = source_entries.get(source_id, {})
            chars_count = entry.get("chars_count", 0)
            lines.append(f"{source_id} ({chars_count} chars)")
        return "\n".join(lines)

    if cmd == "/teacher list":
        profiles = list_teachers()
        lines = [
            f"{profile.id}: {profile.name} ({', '.join(profile.style_tags)})"
            for profile in profiles
        ]
        return "\n".join(lines)

    if cmd == "/teacher show":
        profile = context.teacher_profile
        tags = ", ".join(profile.style_tags)
        return f"{profile.id}: {profile.name} ({tags}) - {profile.intro_line}"

    if cmd.startswith("/teacher set "):
        teacher_id = cmd.replace("/teacher set ", "", 1).strip()
        profile = get_teacher_profile(teacher_id)
        if not profile:
            return "Unknown teacher id."
        context.teacher_id = profile.id
        context.teacher_profile = profile
        memory = load_memory(context.memory_path)
        memory.preferences["teacher_id"] = profile.id
        save_memory(context.memory_path, memory)
        return f"Teacher set to {profile.id}"

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
    response = reply(
        context.persona_text,
        context.engine.strictness,
        state,
        topic_hint,
        subject=context.subject,
        level=context.level,
    )
    intro_line = context.teacher_profile.intro_line
    if intro_line:
        return f"{intro_line} {response}".strip()
    return response


def _ask_next_question(context: CliContext) -> str:
    question = _generate_question(context)
    context.session.last_question = question.text
    context.session.last_question_meta = question.meta
    context.session.questions_asked_count += 1
    return question.text


def _generate_question(context: CliContext) -> Question:
    memory = load_memory(context.memory_path)
    topic = context.topic
    if not topic and context.sources:
        topic = suggest_topic(context.sources)
    prefer_easy = _should_prefer_easy(memory, context.subject, topic)
    if context.llm_enabled:
        source_chunks = build_source_chunks(context.sources)
        llm_question = generate_llm_question(
            context.subject,
            context.level,
            topic,
            context.engine.strictness,
            sources=source_chunks,
            model=context.llm_model,
        )
        if llm_question:
            return llm_question
    return generate_question(
        context.subject,
        context.level,
        topic,
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
    saved_llm_enabled = prefs.get("llm_enabled")
    saved_llm_model = prefs.get("llm_model")
    saved_voice_enabled = prefs.get("voice_enabled")
    saved_teacher_id = prefs.get("teacher_id")
    saved_teacher_profile = get_teacher_profile(saved_teacher_id) or default_teacher()
    context = CliContext(
        engine=TeacherEngine(),
        session=LessonSession(),
        memory_path=MEMORY_PATH,
        persona_text=persona_text,
        teacher_id=saved_teacher_profile.id,
        teacher_profile=saved_teacher_profile,
        topic=saved_topic if saved_topic else None,
        subject=saved_subject if saved_subject else None,
        level=saved_level if saved_level else None,
        llm_enabled=True if saved_llm_enabled is True else False,
        llm_model=saved_llm_model if isinstance(saved_llm_model, str) and saved_llm_model else DEFAULT_MODEL,
        voice_enabled=True if saved_voice_enabled is True else False,
        sources=memory.sources if memory.sources else [],
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
