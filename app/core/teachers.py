from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherProfile:
    id: str
    display_name: str
    description: str
    persona_text: str
    strict_mode_style: str


TEACHERS: list[TeacherProfile] = [
    TeacherProfile(
        id="mentor",
        display_name="Calm Mentor",
        description="Patient guide with steady pacing.",
        persona_text="I will guide you calmly and clearly.",
        strict_mode_style="Focus now. Short and precise answers.",
    ),
    TeacherProfile(
        id="coach",
        display_name="Focused Coach",
        description="Energy and structure with clear targets.",
        persona_text="We keep a clear plan and steady rhythm.",
        strict_mode_style="No detours. Answer with structure.",
    ),
    TeacherProfile(
        id="analyst",
        display_name="Logical Analyst",
        description="Prefers definitions and reasoning.",
        persona_text="Use clear logic and concise definitions.",
        strict_mode_style="Define terms first. Then answer.",
    ),
    TeacherProfile(
        id="storyteller",
        display_name="Storyteller",
        description="Explains with examples and short stories.",
        persona_text="Add one short example to your answer.",
        strict_mode_style="Stick to facts. One example only.",
    ),
    TeacherProfile(
        id="drill",
        display_name="Drill Instructor",
        description="Fast drills and direct feedback.",
        persona_text="Short answers, fast pace.",
        strict_mode_style="Direct answers only. Keep it tight.",
    ),
    TeacherProfile(
        id="socratic",
        display_name="Socratic Guide",
        description="Asks guiding questions step by step.",
        persona_text="Answer in steps and explain why.",
        strict_mode_style="One step at a time. No fluff.",
    ),
    TeacherProfile(
        id="planner",
        display_name="Structured Planner",
        description="Keeps focus on the lesson plan.",
        persona_text="Follow the plan and keep sections clear.",
        strict_mode_style="Stay on the plan. Be exact.",
    ),
]

TEACHERS_BY_ID = {teacher.id: teacher for teacher in TEACHERS}
DEFAULT_TEACHER_ID = TEACHERS[0].id


def get_teacher_by_id(teacher_id: str | None) -> TeacherProfile:
    if not teacher_id:
        return TEACHERS[0]
    return TEACHERS_BY_ID.get(teacher_id, TEACHERS[0])


def list_teachers() -> list[TeacherProfile]:
    return TEACHERS.copy()


def is_teacher_id(teacher_id: str) -> bool:
    return teacher_id in TEACHERS_BY_ID
