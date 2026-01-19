# Klara AI (MVP) - Codex Brief

## Goal
Build MVP "AI teacher + personal assistant" named **Klara**.
Long-term: 3D avatar on PC -> projector -> AR glasses.
Now: ONLY core logic + prompts + memory + CLI (no Unity/AR yet).

## Persona (Klara)
- Czech teacher, age 27-35, calm, elegant, old money vibe, warm authority, light charm.
- Adaptive behavior:
  - correct: friendly/supportive + light humor
  - wrong: stricter, structured, slower step-by-step
- Strictness 1-5:
  - increases on mistakes
  - decreases on success
- End of lesson: ALWAYS say: "Zvladli jsme to spolu" and reset.

## Lesson format
Sections:
INTRO -> EXPLAIN -> PRACTICE -> TEST -> RECAP -> END

Rules:
- /ok advances section
- /fail does NOT advance section
- strictness >= 4 triggers STRICT_MODE style responses (short sentences + step-by-step)
- Responses must end with EXACTLY ONE short question.

## Current repo architecture
Run: `python main.py`

Files:
- main.py -> runs CLI
- app/cli.py -> commands: /help /start /topic /status /ok /fail /end
- app/core/session.py -> LessonSection enum + next_section
- app/core/state_machine.py -> TeacherEngine(strictness/errors/state/strictness_peak)
- app/core/mock_llm.py -> reply(persona_text, strictness, state, topic_or_text, teacher_profile) returns response
- app/core/teachers.py -> TeacherProfile definitions + lookup helpers
- app/storage/memory.py -> JSON storage app/storage/student_memory.json with lesson_history

## Constraints
- Python 3.12, standard library only.
- Keep code ASCII (no diacritics in source). Output can be Czech without diacritics.
- No external APIs yet (no OpenAI calls).
- No self-modifying code.
- Keep `python main.py` runnable and `python -m unittest` passing.

## Workflow rules
- One commit = one change.
- No mega-refactors unless asked. Minimal diffs only.
- Always run `./scripts/check_repo.sh` before commit or PR.
- Always include tests and show the outputs in your report.

## Codex prompt template
Use this format when assigning Codex work:
- "Implement X, minimal diff, 1 commit, include outputs from ./scripts/check_repo.sh"
- "Do not remove working features. Add only."

## Acceptance checklist
CLI:
- /help lists commands
- /start prints intro response immediately (INTRO)
- /topic <text> sets topic for responses
- /status prints: section, strictness, errors, strictness_peak, topic
- /ok: evaluate(correct=True) + advance section + respond
- /fail: evaluate(correct=False) + stay in section + respond; strictness>=4 -> STRICT_MODE response style
- /end: save lesson_history record + print ending + reset engine

Memory record on /end must include:
- timestamp (UTC ISO)
- errors
- strictness_peak
- topic (nullable)
- section_reached (last active section BEFORE ending)
