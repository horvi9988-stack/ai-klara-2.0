"""Streamlit GUI for Klara AI Tutoring System."""

from __future__ import annotations

import html
import tempfile
from collections import defaultdict
from pathlib import Path

import streamlit as st

from app.cli import CliContext, handle_command
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.llm.ollama_client import DEFAULT_MODEL
from app.storage.memory import load_memory
from app.core.local_sources import ingest_file


# Page config
st.set_page_config(
    page_title="Klara AI - Tutoring System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

MEMORY_PATH = Path(__file__).resolve().parent / "app" / "storage" / "student_memory.json"
PROMPT_PATH = Path(__file__).resolve().parent / "app" / "prompts" / "klara.txt"


def init_session_state() -> None:
    """Initialize Streamlit session state."""
    if "context" not in st.session_state:
        persona_text = ""
        if PROMPT_PATH.exists():
            persona_text = PROMPT_PATH.read_text(encoding="utf-8").strip()
        
        memory = load_memory(MEMORY_PATH)
        prefs = memory.preferences if isinstance(memory.preferences, dict) else {}
        
        saved_topic = prefs.get("topic")
        saved_subject = prefs.get("subject")
        saved_level = prefs.get("level")
        saved_llm_enabled = prefs.get("llm_enabled")
        saved_llm_model = prefs.get("llm_model")
        saved_voice_enabled = prefs.get("voice_enabled")
        saved_mode = prefs.get("mode", "teacher")
        
        context = CliContext(
            engine=TeacherEngine(),
            session=LessonSession(),
            memory_path=MEMORY_PATH,
            persona_text=persona_text,
            topic=saved_topic if saved_topic else None,
            subject=saved_subject if saved_subject else None,
            level=saved_level if saved_level else None,
            llm_enabled=True if saved_llm_enabled is True else False,
            llm_model=saved_llm_model if isinstance(saved_llm_model, str) and saved_llm_model else DEFAULT_MODEL,
            voice_enabled=True if saved_voice_enabled is True else False,
            mode=saved_mode if saved_mode in {"teacher", "assistant"} else "teacher",
        )
        st.session_state.context = context
        st.session_state.chat_history = []
        st.session_state.last_response = None
        st.session_state.active_citation_id = None


def apply_theme() -> None:
    """Apply custom UI styling."""
    st.markdown(
        """
        <style>
            .main {
                background: #F8FAFC;
            }
            .app-title {
                font-weight: 700;
                letter-spacing: -0.02em;
                color: #111827;
            }
            .panel-card {
                background: #FFFFFF;
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 24px;
                padding: 18px 20px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            }
            .panel-muted {
                color: #64748B;
                font-size: 0.9rem;
            }
            .chip {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                margin-right: 8px;
                border-radius: 999px;
                border: 1px solid rgba(15, 23, 42, 0.2);
                background: #F1F5F9;
                color: #111827;
                font-size: 0.85rem;
                font-weight: 600;
            }
            .chat-bubble {
                padding: 12px 16px;
                border-radius: 20px;
                margin-bottom: 8px;
                line-height: 1.5;
            }
            .chat-user {
                background: #111827;
                color: #FFFFFF;
            }
            .chat-assistant {
                background: #FFFFFF;
                border: 1px solid rgba(15, 23, 42, 0.08);
                color: #111827;
            }
            .section-title {
                font-weight: 600;
                color: #111827;
            }
            .ios-segmented label {
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_state_display(context: CliContext) -> str:
    """Format context state for display."""
    llm_state = "on" if context.llm_enabled else "off"
    voice_state = "on" if context.voice_enabled else "off"
    return (
        f"**Subject**: {context.subject or 'unset'} | "
        f"**Level**: {context.level or 'unset'} | "
        f"**Topic**: {context.topic or 'unset'} | "
        f"**Mode**: {context.mode} | "
        f"**Strictness**: {context.engine.strictness}\n"
        f"**Section**: {context.session.current_section} | "
        f"**Errors**: {context.engine.errors} | "
        f"**LLM**: {llm_state} | "
        f"**Voice**: {voice_state}"
    )


def render_card(title: str, body: str, footer: str | None = None) -> None:
    footer_html = f"<div class='panel-muted'>{footer}</div>" if footer else ""
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="section-title">{html.escape(title)}</div>
            <div style="margin-top:8px;">{body}</div>
            {footer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def chunk_catalog(context: CliContext) -> list[dict[str, str]]:
    catalog = []
    for index, chunk in enumerate(context.sources, 1):
        source_name = Path(chunk.source).name
        label = f"{source_name} · chunk {index}"
        catalog.append(
            {
                "id": f"{source_name}-{index}",
                "label": label,
                "text": chunk.text,
                "source": source_name,
            }
        )
    return catalog


def render_source_chips(context: CliContext, limit: int = 3) -> None:
    catalog = chunk_catalog(context)
    if not catalog:
        st.markdown("<span class='panel-muted'>Bez citací (zatím žádné zdroje).</span>", unsafe_allow_html=True)
        return
    chips = catalog[:limit]
    columns = st.columns(len(chips))
    for column, chip in zip(columns, chips):
        with column:
            if st.button(f"📄 {chip['label']}", key=f"chip_{chip['id']}"):
                st.session_state.active_citation_id = chip["id"]
    active = next((chip for chip in catalog if chip["id"] == st.session_state.active_citation_id), None)
    if active:
        with st.expander(f"Citace: {active['label']}", expanded=True):
            st.write(active["text"])
            if st.button("Použít jako kontext", key=f"use_context_{active['id']}"):
                response = f"✅ Kontext přidán: {active['label']}"
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
                st.rerun()


def render_chat_message(role: str, message: str) -> None:
    escaped = html.escape(message)
    css_class = "chat-user" if role == "user" else "chat-assistant"
    st.markdown(
        f"<div class='chat-bubble {css_class}'>{escaped}</div>",
        unsafe_allow_html=True,
    )


def render_dashboard(context: CliContext) -> None:
    st.markdown("### Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        render_card(
            "Dnes",
            "<strong>1 doporučená lekce</strong><br/>Krátký warm‑up k tématu.",
            "Tip: držet tempo 25–30 min.",
        )
    with col2:
        render_card(
            "Slabiny",
            "<strong>2 okruhy</strong><br/>Makroekonomie · Elasticita.",
            "Poslední kontrola: dnes ráno.",
        )
    with col3:
        render_card(
            "Deadline",
            "<strong>3 úkoly</strong><br/>Seminářka · Test · Čtení.",
            "Auto‑plán dne dostupný v Tasks.",
        )
    st.markdown("### Přehled")
    col4, col5 = st.columns([2, 1])
    with col4:
        render_card(
            "Doporučená lekce",
            "Prohloubit vztah Ingestace → Chunk → Citace a jejich roli v Tutor Mode.",
            "Naposledy: včera 18:20.",
        )
    with col5:
        render_card(
            "Režim",
            f"<strong>{context.mode.title()}</strong><br/>Přísnost: {context.engine.strictness}/5",
            "Přepni režim v profilu.",
        )


def render_materials(context: CliContext) -> None:
    st.markdown("### Materials")
    st.markdown("<div class='panel-muted'>Lokální soubory a ingestace (offline).</div>", unsafe_allow_html=True)

    uploads_dir = Path(__file__).resolve().parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Přidat dokument (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            key="file_uploader_main",
        )
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            try:
                chunks = ingest_file(Path(tmp_path))
                if chunks:
                    context.sources.extend(chunks)
                    msg = f"✅ Nahráno {uploaded_file.name}: {len(chunks)} chunků"
                    st.session_state.chat_history.append(("system", msg))
                    st.session_state.last_response = msg
                    st.success(msg)
                else:
                    msg = "❌ Soubor neobsahuje čitelný text."
                    st.session_state.chat_history.append(("system", msg))
                    st.error(msg)
            except Exception as exc:
                msg = f"❌ Chyba ingestace: {exc}"
                st.session_state.chat_history.append(("system", msg))
                st.error(msg)
            finally:
                Path(tmp_path).unlink()
    with col2:
        if st.button("Vyčistit nahrané zdroje"):
            context.sources.clear()
            st.success("Zdrojové chunky vyčištěny.")

    st.markdown("#### Lokální soubory")
    files = [f for f in uploads_dir.iterdir() if f.is_file() and not f.name.startswith("lesson_")]
    if files:
        for file in files:
            render_card(
                file.name,
                f"Velikost: {file.stat().st_size // 1024} KB",
                "Připraveno k ingestaci.",
            )
    else:
        st.info("Zatím nejsou žádné lokální soubory.")

    st.markdown("#### Ingestované chunky")
    if context.sources:
        grouped: dict[str, int] = defaultdict(int)
        for chunk in context.sources:
            grouped[Path(chunk.source).name] += 1
        for source, count in grouped.items():
            render_card(source, f"{count} chunků", "Metadata: source + index.")
    else:
        st.info("Žádné chunky nejsou načtené.")


def render_tasks(context: CliContext) -> None:
    st.markdown("### Tasks")
    st.markdown("<div class='panel-muted'>Agenda s týdenním pohledem.</div>", unsafe_allow_html=True)
    if st.button("Auto‑plán dne"):
        response = "✅ Dnešní plán byl připraven (offline simulace)."
        st.session_state.chat_history.append(("system", response))
        st.session_state.last_response = response

    days = ["Po", "Út", "St", "Čt", "Pá"]
    day_cols = st.columns(5)
    for day, col in zip(days, day_cols):
        with col:
            render_card(day, "• Studium 45 min<br/>• Opakování 15 min", "iOS‑style blok.")

    st.markdown("#### Todo list (Assistant Mode)")
    memory = load_memory(MEMORY_PATH)
    if memory.todos:
        for i, todo in enumerate(memory.todos, 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i}. {todo}")
            with col2:
                if st.button("✓", key=f"todo_task_{i}"):
                    response = handle_command(context, f"/todo done {i}")
                    st.session_state.chat_history.append(("system", response))
                    st.rerun()
    else:
        st.info("Žádné úkoly nejsou přidané.")

    st.markdown("#### Přidat úkol")
    todo_text = st.text_input("Nový úkol:", key="todo_input_tasks")
    if st.button("Přidat úkol"):
        if todo_text:
            response = handle_command(context, f"/todo add {todo_text}")
            st.session_state.chat_history.append(("system", response))
            st.rerun()


def render_profile(context: CliContext) -> None:
    st.markdown("### Profile")
    st.markdown("<div class='panel-muted'>Nastavení režimu, přísnosti a hlasu.</div>", unsafe_allow_html=True)

    st.markdown("#### Režim")
    mode = st.radio(
        "Zvol režim:",
        ["teacher", "assistant"],
        index=0 if context.mode == "teacher" else 1,
        key="mode_selector_main",
        horizontal=True,
    )
    if mode != context.mode:
        response = handle_command(context, f"/mode {mode}")
        st.session_state.chat_history.append(("system", response))
        st.session_state.last_response = response

    st.markdown("#### Přísnost")
    strictness = st.slider("Přísnost (1–5)", 1, 5, context.engine.strictness, key="strictness_slider")
    if strictness != context.engine.strictness:
        context.engine.strictness = strictness
        response = f"✅ Přísnost nastavena na {strictness}."
        st.session_state.chat_history.append(("system", response))
        st.session_state.last_response = response

    st.markdown("#### Hlas")
    voice_enabled = st.checkbox("Hlasový výstup", value=context.voice_enabled, key="voice_toggle")
    if voice_enabled != context.voice_enabled:
        cmd = "/voice on" if voice_enabled else "/voice off"
        response = handle_command(context, cmd)
        st.session_state.chat_history.append(("system", response))
        st.session_state.last_response = response


def render_tutor_mode(context: CliContext) -> None:
    st.markdown("### Tutor Mode")

    st.markdown("#### Stav lekce")
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**State**: {format_state_display(context)}")
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()

    st.markdown("#### Konverzace")
    chat_container = st.container()
    with chat_container:
        for role, message in st.session_state.chat_history:
            render_chat_message(role, message)
            if role != "user":
                st.markdown("<div class='panel-muted'>Source Chips</div>", unsafe_allow_html=True)
                render_source_chips(context)

    st.markdown("#### Vstup")
    if context.session.last_question:
        placeholder = "Napiš odpověď…"
        help_text = "📝 Odpověz na otázku."
    else:
        placeholder = "Napiš příkaz (/start) nebo text."
        help_text = "💬 Příkaz nebo zpráva."

    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input(help_text, placeholder=placeholder, key="command_input_main")
    with col2:
        submit = st.button("Odeslat", use_container_width=True)

    if submit and user_input:
        if context.session.last_question:
            response = handle_command(context, f"/answer {user_input}")
        else:
            response = handle_command(context, user_input)

        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("system", response))
        st.session_state.last_response = response
        st.rerun()

    st.markdown("#### Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Nápověda"):
            response = handle_command(context, "/help")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    with col2:
        if st.button("Další téma"):
            response = handle_command(context, "/next")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    with col3:
        if st.button("Začít lekci"):
            response = handle_command(context, "/start")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    with col4:
        if st.button("Ukončit"):
            response = handle_command(context, "/end")
            st.session_state.chat_history.append(("system", response))
            st.rerun()


def main() -> None:
    """Main Streamlit app."""
    init_session_state()
    context = st.session_state.context

    apply_theme()

    st.markdown("<h1 class='app-title'>Klara AI</h1>", unsafe_allow_html=True)
    st.markdown("<div class='panel-muted'>iOS Settings look & feel · Old Money elegance · Offline‑first</div>", unsafe_allow_html=True)

    tabs = st.tabs(["Dashboard", "Tutor Mode", "Materials", "Tasks", "Profile"])
    with tabs[0]:
        render_dashboard(context)
    with tabs[1]:
        render_tutor_mode(context)
    with tabs[2]:
        render_materials(context)
    with tabs[3]:
        render_tasks(context)
    with tabs[4]:
        render_profile(context)

    if st.session_state.last_response:
        st.divider()
        st.info(st.session_state.last_response)


if __name__ == "__main__":
    main()
