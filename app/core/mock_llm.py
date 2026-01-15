from __future__ import annotations

from app.core.session import LessonSection


SECTION_PROMPTS = {
    LessonSection.INTRO: "Today we set the goal and focus the topic.",
    LessonSection.EXPLAIN: "I will explain the key idea clearly.",
    LessonSection.PRACTICE: "Now we practice together with guidance.",
    LessonSection.TEST: "Show me you can apply it on your own.",
    LessonSection.RECAP: "We summarize the main points and fix gaps.",
    LessonSection.END: "We close the lesson with confidence.",
}

SECTION_QUESTIONS = {
    LessonSection.INTRO: "What do you want to achieve today?",
    LessonSection.EXPLAIN: "What is the main idea in your own words?",
    LessonSection.PRACTICE: "Can you try one example now?",
    LessonSection.TEST: "What is your final answer?",
    LessonSection.RECAP: "What is one key point you will remember?",
    LessonSection.END: "Are you ready to close the lesson?",
}


def _supportive_line() -> str:
    return "Good work so far. I see your effort, and I will guide you."


def _light_humor() -> str:
    return "No drama, we fix it together. Even my chalk makes mistakes."


def _neutral_line() -> str:
    return "We will proceed step by step with a clear structure."


def _strict_line() -> str:
    return "Focus. Short answers. One step at a time."


def reply(persona_text: str, strictness: int, state: LessonSection, user_text: str) -> str:
    section_line = SECTION_PROMPTS.get(state, "We continue the lesson.")
    question = SECTION_QUESTIONS.get(state, "What is your next step?")

    if strictness <= 2:
        tone = _supportive_line() + _light_humor()
        parts = [
            persona_text.strip(),
            tone.strip(),
            section_line.strip(),
        ]
    elif strictness == 3:
        tone = _neutral_line()
        parts = [
            persona_text.strip(),
            tone.strip(),
            section_line.strip(),
        ]
    else:
        parts = [
            persona_text.strip(),
            _strict_line().strip(),
            "Step 1: Name the key idea.",
            "Step 2: Give one short example.",
        ]

    if user_text:
        parts.append(f"I heard: {user_text.strip()}.")
    parts.append(question.strip())

    response = " ".join(part for part in parts if part)
    return response
