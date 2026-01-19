from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherProfile:
    id: str
    name: str
    vibe: str
    strictness_style: str
    catchphrases: list[str]
    subject_preferences: list[str]


TEACHER_PROFILES: list[TeacherProfile] = [
    TeacherProfile(
        id="klara",
        name="Klara",
        vibe="calm, warm authority, elegant",
        strictness_style="balanced",
        catchphrases=["Drzime tempo.", "Jdeme na to krok za krokem."],
        subject_preferences=["dejepis", "anglictina", "programovani"],
    ),
    TeacherProfile(
        id="professor",
        name="Profesor Novak",
        vibe="formal, academic, detail-first",
        strictness_style="strict",
        catchphrases=["Bez odbocek.", "Presnost nade vse."],
        subject_preferences=["matematika", "fyzika", "ekonomie"],
    ),
    TeacherProfile(
        id="coach",
        name="Coach Marek",
        vibe="motivational, sporty, focused",
        strictness_style="coach",
        catchphrases=["Makame dal.", "Drzime fokus."],
        subject_preferences=["matematika", "programovani", "anglictina"],
    ),
    TeacherProfile(
        id="funny",
        name="Vtipny Tutor",
        vibe="light humor, friendly",
        strictness_style="funny",
        catchphrases=["Dame tomu usmev.", "Bude to rychlovka."],
        subject_preferences=["dejepis", "ekonomie", "anglictina"],
    ),
    TeacherProfile(
        id="strict",
        name="Prisma Pani",
        vibe="strict, no-nonsense, clear rules",
        strictness_style="strict",
        catchphrases=["Strucne.", "Pravidla plati."],
        subject_preferences=["matematika", "dejepis", "programovani"],
    ),
]


def list_teacher_profiles() -> list[TeacherProfile]:
    return list(TEACHER_PROFILES)


def find_teacher_profile(teacher_id: str) -> TeacherProfile | None:
    cleaned = teacher_id.strip().lower()
    for profile in TEACHER_PROFILES:
        if profile.id == cleaned:
            return profile
    return None


def get_teacher_profile(teacher_id: str | None) -> TeacherProfile:
    if teacher_id:
        profile = find_teacher_profile(teacher_id)
        if profile:
            return profile
    return TEACHER_PROFILES[0]
