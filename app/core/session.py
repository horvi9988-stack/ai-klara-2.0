from __future__ import annotations

from enum import Enum


class LessonSection(str, Enum):
    INTRO = "INTRO"
    EXPLAIN = "EXPLAIN"
    PRACTICE = "PRACTICE"
    TEST = "TEST"
    RECAP = "RECAP"
    END = "END"

    def next_section(self) -> "LessonSection":
        order = [
            LessonSection.INTRO,
            LessonSection.EXPLAIN,
            LessonSection.PRACTICE,
            LessonSection.TEST,
            LessonSection.RECAP,
            LessonSection.END,
        ]
        index = order.index(self)
        return order[min(index + 1, len(order) - 1)]
