from __future__ import annotations

"""Lesson session state and section helpers."""

from dataclasses import dataclass, field

from app.core.question_engine import QuestionMeta


SECTIONS = ["INTRO", "EXPLAIN", "PRACTICE", "TEST", "RECAP", "END"]


SECTION_ACTIONS = {
    "INTRO": "Uvitani a rychly prehled tematu.",
    "EXPLAIN": "Vysvetleni latky krok po kroku.",
    "PRACTICE": "Rizena praxe se zadanim a napovedami.",
    "TEST": "Kratsi overeni znalosti bez napoved.",
    "RECAP": "Strucne shrnuti a ujasneni pojmu.",
    "END": "Pozitivni zaver a rozlouceni.",
}


@dataclass
class LessonSession:
    sections: list[str] = field(default_factory=lambda: SECTIONS.copy())
    index: int = 0
    questions_asked_count: int = 0
    last_question: str | None = None
    last_question_meta: QuestionMeta | None = None
    last_answer: str | None = None
    ok_count: int = 0
    fail_count: int = 0

    @property
    def current_section(self) -> str:
        return self.sections[self.index]

    def action_for_current(self) -> str:
        return SECTION_ACTIONS.get(self.current_section, "Pokracujeme v lekci.")

    def next_section(self) -> tuple[str, str]:
        if self.index < len(self.sections) - 1:
            self.index += 1
        section = self.current_section
        return section, SECTION_ACTIONS.get(section, "Pokracujeme v lekci.")

    def reset(self) -> None:
        self.index = 0
        self.questions_asked_count = 0
        self.last_question = None
        self.last_question_meta = None
        self.last_answer = None
        self.ok_count = 0
        self.fail_count = 0
