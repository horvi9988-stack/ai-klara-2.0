from __future__ import annotations

from app.core.teachers import TeacherProfile


def reply(
    persona_text: str,
    strictness: int,
    state: str,
    user_text: str,
    subject: str | None = None,
    level: str | None = None,
    teacher_profile: TeacherProfile | None = None,
) -> str:
    tone = _tone(strictness, teacher_profile)
    persona_hint = _persona_hint(persona_text, teacher_profile)
    teacher_hint = _teacher_hint(teacher_profile)
    topic_hint = _topic_hint(user_text)
    subject_label = subject or "obecne"
    level_label = level or "nezadana"
    context_line = f"Zamerime se na {subject_label} na urovni {level_label}."
    if strictness >= 4:
        steps = _strict_steps(subject_label, topic_hint)
        question = _question_for(subject_label, level_label, state)
        return " ".join(
            [tone, persona_hint, teacher_hint, context_line, steps, question]
        ).strip()
    mini_task = _mini_task(subject_label, topic_hint, state)
    question = _question_for(subject_label, level_label, state)
    return " ".join(
        [tone, persona_hint, teacher_hint, context_line, mini_task, question]
    ).strip()


def _tone(strictness: int, teacher_profile: TeacherProfile | None) -> str:
    style_line = _teacher_style_line(teacher_profile)
    if strictness <= 2:
        base = "Jsi sikovny, jedeme dal."
        return " ".join([style_line, base]).strip()
    if strictness == 3:
        base = "Budeme peclivi a jasni."
        return " ".join([style_line, base]).strip()
    base = "Ted budu prisna a povedu te krok po kroku."
    return " ".join([style_line, base]).strip()


def _strict_steps(subject: str, topic: str) -> str:
    step_1 = f"Krok 1: zopakuj si zakladni pojmy pro {subject}."
    step_2 = f"Krok 2: udelej mini-ukol k {topic}."
    return f"{step_1} {step_2}"


def _mini_task(subject: str, topic: str, state: str) -> str:
    if subject == "dejepis":
        return f"Mini-ukol: shrn 2 fakta o {topic}."
    if subject == "matematika":
        return "Mini-ukol: priprav postup vypoctu."
    if subject == "ekonomie":
        return "Mini-ukol: uved 1 priklad z praxe."
    if subject == "anglictina":
        return "Mini-ukol: preloz kratkou vetu do AJ."
    if subject == "programovani":
        return "Mini-ukol: navrhni jednoduchy algoritmus."
    if state == "END":
        return "Mini-ukol: priprav kratke shrnuti."
    return "Mini-ukol: udelej kratke opakovani."


def _question_for(subject: str, level: str, state: str) -> str:
    if subject == "dejepis":
        return _question_dejepis(level, state)
    if subject == "matematika":
        return _question_matematika(level, state)
    if subject == "ekonomie":
        return _question_ekonomie(level, state)
    if subject == "anglictina":
        return _question_anglictina(level, state)
    if subject == "programovani":
        return _question_programovani(level, state)
    return "Jak bys to vysvetlil jednou vetou?"


def _question_dejepis(level: str, state: str) -> str:
    if level == "zakladni":
        return "Kdo byl Karel IV a proc je dulezity?"
    if level == "stredni":
        return "Jaky byl dopad prumyslove revoluce na spolecnost?"
    if level in {"vysoka", "magisterska"}:
        return "Porovnej pricinny retezec udalosti vedoucich k 1. svetove valce?"
    if level == "maturita":
        return "Jak bys obhajil vyznam Mnichovske dohody?"
    if level == "bakalarska":
        return "Srovnej 2 pristupy k interpretaci husitstvi?"
    if state == "END":
        return "Co si z teto lekce odnasite?"
    return "Ktera udalost zmenila dejiny nejvic?"


def _question_matematika(level: str, state: str) -> str:
    if level == "zakladni":
        return "Vypocitej 12 * 7?"
    if level == "stredni":
        return "Vyres rovnici 2x + 5 = 17?"
    if level in {"vysoka", "magisterska"}:
        return "Derivuj f(x)=x^3 * ln(x)?"
    if level == "maturita":
        return "Spocitej limitu lim x->0 (sin x)/x?"
    if level == "bakalarska":
        return "Najdi integral z 2x e^(x^2) dx?"
    if state == "END":
        return "Ktery postup ti dnes fungoval nejlepe?"
    return "Jaky je dalsi krok ve vypoctu?"


def _question_ekonomie(level: str, state: str) -> str:
    if level == "zakladni":
        return "Co je inflace jednou vetou?"
    if level == "stredni":
        return "Co je inflace a jak vznika?"
    if level in {"vysoka", "magisterska"}:
        return "Vysvetli IS-LM model v jedne vete a dej 1 priklad dopadu fiskalni expanze?"
    if level == "maturita":
        return "Jak bys popsal roli centralni banky?"
    if level == "bakalarska":
        return "Uved 1 vyhodu a 1 riziko globalizace?"
    if state == "END":
        return "Jaky pojem byl nejtazsi?"
    return "Kde bys to videl v realnem zivote?"


def _question_anglictina(level: str, state: str) -> str:
    if level == "zakladni":
        return "Preloz vetu 'I go to school every day'?"
    if level == "stredni":
        return "Jaky je rozdil mezi past simple a present perfect?"
    if level in {"vysoka", "magisterska"}:
        return "Jak bys vysvetlil roli pragmatiky v beznem hovoru?"
    if level == "maturita":
        return "Popis rozdil mezi formalni a neformalni anglictinou?"
    if level == "bakalarska":
        return "Jak bys analyzoval ton autora v kratkem textu?"
    if state == "END":
        return "Na cem chces v AJ pracovat dal?"
    return "Ktera cast gramatiky ti dela problem?"


def _question_programovani(level: str, state: str) -> str:
    if level == "zakladni":
        return "Co je to promenna v programovani?"
    if level == "stredni":
        return "Jak funguje cyklus for v Pythonu?"
    if level in {"vysoka", "magisterska"}:
        return "Popis slozitost O(n log n) na prikladu trideni?"
    if level == "maturita":
        return "Jak bys vysvetlil rozdil mezi stack a heap?"
    if level == "bakalarska":
        return "Proc jsou testy dulezite pri vyvoji software?"
    if state == "END":
        return "Ktery koncept si zopakujeme priste?"
    return "Jak bys to implementoval jednoduse?"


def _topic_hint(user_text: str) -> str:
    cleaned = user_text.strip()
    if not cleaned:
        return "tematu"
    return cleaned


def _persona_hint(persona_text: str, teacher_profile: TeacherProfile | None) -> str:
    cleaned = persona_text.strip()
    if not cleaned:
        if teacher_profile:
            return f"Jsem {teacher_profile.name}."
        return ""
    if teacher_profile:
        return f"Jsem {teacher_profile.name}."
    return "Jsem Klara."


def _teacher_style_line(teacher_profile: TeacherProfile | None) -> str:
    if not teacher_profile:
        return ""
    style = teacher_profile.strictness_style
    if style == "strict":
        return "Strucne a presne."
    if style == "supportive":
        return "Jsem tu pro tebe."
    if style == "coach":
        return "Makame disciplinovane."
    if style == "funny":
        return "Dneska to dame s nadhledem."
    return ""


def _teacher_hint(teacher_profile: TeacherProfile | None) -> str:
    if not teacher_profile:
        return ""
    if teacher_profile.catchphrases:
        return teacher_profile.catchphrases[0]
    return ""
