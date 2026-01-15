# Tasks for Codex (do one at a time)

## Task A - Add persistent "topic" into memory
- Store last topic under memory key: preferences.topic
- On startup load last topic automatically
- Keep backward compatibility with existing JSON

## Task B - Improve Czech "old money" persona (safe)
- Update app/prompts/klara.txt to better match: calm, elegant, authoritative, light charm
- Ensure mock_llm uses persona text but still ends with exactly one question

## Task C - Teacher vs Assistant mode (next big step)
Add:
- /mode teacher (default)
- /mode assistant
Assistant commands:
- /todo add <text>
- /todo list
- /todo done <index>
Persist todos in memory (key: todos [])
