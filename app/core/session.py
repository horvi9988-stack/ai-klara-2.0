from __future__ import annotations

from dataclasses import dataclass, field


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
