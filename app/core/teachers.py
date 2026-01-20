from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherProfile:
    id: str
    name: str
    style_tags: list[str]
    intro_line: str


TEACHER_PROFILES = [
    TeacherProfile(
        id="klara",
        name="Klara",
        style_tags=["calm", "structured", "encouraging"],
        intro_line="I will guide you step by step.",
    ),
    TeacherProfile(
        id="milan",
        name="Milan",
        style_tags=["direct", "efficient", "focused"],
        intro_line="We will stay focused and move fast.",
    ),
    TeacherProfile(
        id="hana",
        name="Hana",
        style_tags=["patient", "supportive", "clear"],
        intro_line="Take your time, we will build it together.",
    ),
    TeacherProfile(
        id="viktor",
        name="Viktor",
        style_tags=["challenging", "precise", "strict"],
        intro_line="I will challenge you with precise questions.",
    ),
    TeacherProfile(
        id="lea",
        name="Lea",
        style_tags=["curious", "creative", "open"],
        intro_line="Let us explore the topic with curiosity.",
    ),
]


def list_teachers() -> list[TeacherProfile]:
    return TEACHER_PROFILES.copy()


def get_teacher_profile(teacher_id: str | None) -> TeacherProfile | None:
    if not teacher_id:
        return None
    for profile in TEACHER_PROFILES:
        if profile.id == teacher_id:
            return profile
    return None


def default_teacher() -> TeacherProfile:
    return TEACHER_PROFILES[0]
