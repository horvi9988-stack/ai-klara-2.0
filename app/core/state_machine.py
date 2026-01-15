from __future__ import annotations

from dataclasses import dataclass

from app.core.session import LessonSection


@dataclass
class TeacherEngine:
    strictness: int = 2
    errors: int = 0
    state: LessonSection = LessonSection.INTRO
    strictness_peak: int = 2

    def start_lesson(self) -> None:
        self.state = LessonSection.INTRO
        self.strictness = 2
        self.errors = 0
        self.strictness_peak = self.strictness

    def evaluate(self, correct: bool) -> None:
        if correct:
            self.strictness = max(1, self.strictness - 1)
        else:
            self.errors += 1
            self.strictness = min(5, self.strictness + 1)
        if self.strictness > self.strictness_peak:
            self.strictness_peak = self.strictness
        if correct:
            self.state = self.state.next_section()

    def end_lesson(self) -> None:
        self.state = LessonSection.END

    def reset(self) -> None:
        self.strictness = 2
        self.errors = 0
        self.state = LessonSection.INTRO
        self.strictness_peak = self.strictness
