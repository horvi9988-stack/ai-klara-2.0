from dataclasses import dataclass
from typing import Optional

from app.storage.memory import MemoryStore


@dataclass
class AppState:
    topic: str


class CliApp:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory
        self.state = self._load_state()

    def _load_state(self) -> AppState:
        memory = self.memory.load()
        preferences = memory.get("preferences", {})
        topic = preferences.get("topic") or "general"
        return AppState(topic=topic)

    def set_topic(self, topic: str) -> str:
        cleaned = topic.strip()
        if not cleaned:
            return "Topic cannot be empty."
        self.state.topic = cleaned
        self.memory.set_topic(cleaned)
        return f"Topic set to {cleaned}."

    def status(self) -> str:
        return f"topic={self.state.topic}"

    def handle_command(self, command: str) -> Optional[str]:
        if command.startswith("/topic "):
            return self.set_topic(command[len("/topic ") :])
        if command == "/status":
            return self.status()
        return None


def main() -> None:
    memory = MemoryStore("app/storage/student_memory.json")
    app = CliApp(memory)
    while True:
        try:
            raw = input("> ").strip()
        except EOFError:
            break
        if raw == "/exit":
            break
        response = app.handle_command(raw)
        if response:
            print(response)
