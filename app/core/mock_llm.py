from __future__ import annotations

from app.core.session import LessonSection


SECTION_LINES = {
    LessonSection.INTRO: "Dnes si nastavime cil a smer lekce.",
    LessonSection.EXPLAIN: "Vysvetlim ti klicovou myslenku jasne a klidne.",
    LessonSection.PRACTICE: "Procivicime to spolu na prikladu.",
    LessonSection.TEST: "Ted to zkus samostatne.",
    LessonSection.RECAP: "Shrneme hlavni body a opravime mezery.",
    LessonSection.END: "Lekci uzavreme s jistotou.",
}

SECTION_QUESTIONS = {
    LessonSection.INTRO: "Jaky cil dnes chces dosahnout?",
    LessonSection.EXPLAIN: "Rekni mi hlavni myslenku vlastnimi slovy?",
    LessonSection.PRACTICE: "Zkusis jeden kratky priklad?",
    LessonSection.TEST: "Jaka je tva konecna odpoved?",
    LessonSection.RECAP: "Jaky je jeden bod, ktery si zapamatujes?",
    LessonSection.END: "Jsi pripravena uzavrit lekci?",
}


def _supportive_tone() -> list[str]:
    return [
        "Dobra prace. Vidim snahu a povedu te.",
        "Zadna drama, i moje krida se obcas splete.",
    ]


def _neutral_tone() -> list[str]:
    return ["Pojdme strukturovane krok za krokem."]


def _strict_tone(state: LessonSection) -> list[str]:
    return [
        "Prisny rezim.",
        f"Sekce {state.value}.",
        "Krok 1: Pojmenuj klicovou myslenku.",
        "Krok 2: Dej jeden kratky priklad.",
    ]


def reply(persona_text: str, strictness: int, state: LessonSection, user_text: str) -> str:
    section_line = SECTION_LINES.get(state, "Pokracujeme v lekci.")
    question = SECTION_QUESTIONS.get(state, "Co udelas jako dalsi krok?")

    if strictness <= 2:
        parts = [persona_text.strip(), section_line] + _supportive_tone()
    elif strictness == 3:
        parts = [persona_text.strip(), section_line] + _neutral_tone()
    else:
        parts = [persona_text.strip()] + _strict_tone(state)

    if user_text:
        parts.append(f"Tema: {user_text.strip()}.")
    parts.append(question.strip())

    response = " ".join(part for part in parts if part)
    return response
