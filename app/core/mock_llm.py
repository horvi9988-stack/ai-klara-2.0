from __future__ import annotations


def reply(persona_text: str, strictness: int, state: str, user_text: str) -> str:
    tone = _tone(strictness)
    step = _step_by_step(state, user_text)
    question = _short_question(state)
    persona_hint = _persona_hint(persona_text)
    return f"{tone} {persona_hint} {step} {question}".strip()


def _tone(strictness: int) -> str:
    if strictness <= 2:
        return "Jsi sikovny, jedeme dal."
    if strictness == 3:
        return "Budeme peclivi a jasni."
    return "Ted budu prisna a povedu te krok po kroku."


def _step_by_step(state: str, user_text: str) -> str:
    topic = _topic_hint(user_text)
    if state == "INTRO":
        return f"Krok 1: kratky prehled tematu {topic}."
    if state == "EXPLAIN":
        return f"Krok 1: definice. Krok 2: priklad z praxe k {topic}."
    if state == "PRACTICE":
        return f"Krok 1: priprav si postup. Krok 2: zkus resit {topic}."
    if state == "TEST":
        return f"Krok 1: precti zadani. Krok 2: odpovez k {topic}."
    if state == "RECAP":
        return "Krok 1: shrneme pojmy. Krok 2: zkontrolujeme postup."
    if state == "STRICT_MODE":
        return f"Krok 1: zastavime se u zakladu. Krok 2: znovu projdeme {topic}."
    if state == "END":
        return "Krok 1: kratke zhodnoceni."
    return f"Krok 1: navazeme na {topic}."


def _short_question(state: str) -> str:
    if state in {"INTRO", "EXPLAIN"}:
        return "Je to jasne?"
    if state == "PRACTICE":
        return "Zkusis to ted?"
    if state == "TEST":
        return "Jdeme na odpoved?"
    if state == "RECAP":
        return "Chces doplnit neco?"
    if state == "STRICT_MODE":
        return "Rozumis tomuhle kroku?"
    if state == "END":
        return "Dam ti kratke domaci cviceni?"
    return "Pokracujeme?"


def _topic_hint(user_text: str) -> str:
    cleaned = user_text.strip()
    if not cleaned:
        return "zakladum"
    return cleaned


def _persona_hint(persona_text: str) -> str:
    cleaned = persona_text.strip()
    if not cleaned:
        return ""
    return "Jsem Klara."
