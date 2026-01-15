from __future__ import annotations

from dataclasses import dataclass


MAX_STRICTNESS = 5
MIN_STRICTNESS = 1


@dataclass
class TeacherEngine:
    strictness: int = MIN_STRICTNESS
    errors: int = 0
    state: str = "INIT"
    strictness_peak: int = MIN_STRICTNESS

    def start_lesson(self) -> None:
        self.strictness = MIN_STRICTNESS
        self.errors = 0
        self.state = "INTRO"
        self.strictness_peak = MIN_STRICTNESS

    def evaluate(self, correct: bool) -> None:
        self.state = "EVALUATE"
        if correct:
            self.strictness = max(MIN_STRICTNESS, self.strictness - 1)
        else:
            self.errors += 1
            self.strictness = min(MAX_STRICTNESS, self.strictness + 1)
            if self.strictness >= 4:
                self.state = "STRICT_MODE"
        self.strictness_peak = max(self.strictness_peak, self.strictness)

    def end_lesson(self) -> str:
        self.state = "END"
        self.strictness = MIN_STRICTNESS
        self.errors = 0
        self.strictness_peak = MIN_STRICTNESS
        return "Dnesek koncime. Zvladli jsme to spolu."

    def reset(self) -> None:
        self.strictness = MIN_STRICTNESS
        self.errors = 0
        self.strictness_peak = MIN_STRICTNESS
        self.state = "INIT"
