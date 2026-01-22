"""Streamlit GUI for Klara AI Tutoring System."""

from __future__ import annotations

import json
import csv
from pathlib import Path

import streamlit as st

from app.cli import CliContext, handle_command
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.llm.ollama_client import DEFAULT_MODEL
from app.storage.memory import load_memory, save_memory
from app.core.local_sources import SourceChunk, ingest_file, retrieve_chunks
from app.core.llm_question_engine import generate_llm_question
from app.core.question_engine import generate_lesson_from_sources, generate_question


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
    if "active_context_chunks" not in st.session_state:
        st.session_state.active_context_chunks = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


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


def _build_retrieval_query(context: CliContext, user_query: str | None) -> str:
    parts = [context.subject, context.topic, user_query]
    return " ".join(part.strip() for part in parts if part and part.strip())


def _clip_text(text: str, limit: int) -> str:
    cleaned = text.replace("\n", " ").strip()
    if limit <= 0:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def _source_label(chunk: SourceChunk) -> str:
    page = chunk.page if chunk.page is not None else 1
    return f"[Zdroj: {chunk.source}, str. {page}]"


def _with_citation_prefix(chunk: SourceChunk) -> SourceChunk:
    citation = _source_label(chunk)
    return SourceChunk(
        text=f"{citation} {chunk.text}",
        source=chunk.source,
        page=chunk.page,
        source_path=chunk.source_path,
    )


def _retrieve_context_chunks(
    context: CliContext,
    user_query: str | None,
    *,
    limit: int = 5,
) -> list[SourceChunk]:
    if not context.sources:
        return []
    query = _build_retrieval_query(context, user_query)
    if not query:
        return context.sources[:limit]
    return retrieve_chunks(context.sources, query, limit=limit)


def _generate_question_from_context(
    context: CliContext,
    context_chunks: list[SourceChunk],
    *,
    preview_len: int = 250,
) -> str:
    if context.llm_enabled:
        llm_question = generate_llm_question(
            context.subject,
            context.level,
            context.topic,
            context.engine.strictness,
            sources=context_chunks,
            model=context.llm_model,
        )
        if llm_question:
            context.session.last_question = llm_question.text
            context.session.last_question_meta = llm_question.meta
            context.session.questions_asked_count += 1
            return llm_question.text
    question = generate_question(
        context.subject,
        context.level,
        context.topic,
        context.engine.strictness,
        sources=context_chunks,
        preview_len=preview_len,
    )
    context.session.last_question = question.text
    context.session.last_question_meta = question.meta
    context.session.questions_asked_count += 1
    return question.text


def main() -> None:
    """Main Streamlit app."""
    init_session_state()
    context = st.session_state.context
    
    st.title("📚 Klara AI - Tutoring System")
    st.markdown(
        """
        <style>
        :root {
            color-scheme: light;
        }
        .ios-section-title {
            color: #6b7280;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
            margin: 0.25rem 0 0.5rem;
        }
        .ios-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
            border: 1px solid #f0f2f5;
        }
        .ios-card + .ios-card {
            margin-top: 1rem;
        }
        .ios-card .stRadio [role="radiogroup"] {
            display: flex;
            gap: 0.5rem;
        }
        .ios-card .stRadio label {
            background: rgba(120, 120, 128, 0.12);
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-weight: 600;
        }
        .ios-card .stSlider > div {
            padding-top: 0.25rem;
        }
        .ios-card .stCheckbox {
            margin-top: 0.25rem;
        }
        .ios-pill {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: #f3f4f6;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .ios-search-result {
            border-radius: 14px;
            padding: 0.75rem;
            border: 1px solid #eef0f3;
            background: #fafafa;
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        tab1, tab2, tab3 = st.tabs(["Settings", "Upload", "History"])
        
        with tab1:
            st.markdown("<div class='ios-section-title'>Chování AI</div>", unsafe_allow_html=True)
            st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
            mode_labels = {"Tutor": "teacher", "Asistent": "assistant"}
            mode_choice = st.radio(
                "Mode",
                list(mode_labels.keys()),
                index=0 if context.mode == "teacher" else 1,
                horizontal=True,
                label_visibility="collapsed",
                key="mode_selector",
            )
            chosen_mode = mode_labels[mode_choice]
            if chosen_mode != context.mode:
                response = handle_command(context, f"/mode {chosen_mode}")
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            st.caption(
                "Režim Tutor vysvětluje krok za krokem. Asistent odpovídá přímočařeji."
            )

            strictness = st.slider(
                "Úroveň přísnosti",
                min_value=1,
                max_value=5,
                value=int(context.engine.strictness),
                step=1,
                key="strictness_slider",
            )
            if strictness != context.engine.strictness:
                context.engine.strictness = strictness
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='ios-section-title'>Technické nastavení</div>", unsafe_allow_html=True)
            st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
            llm_enabled = st.checkbox("Enable LLM", value=context.llm_enabled, key="llm_checkbox")
            if llm_enabled != context.llm_enabled:
                cmd = "/llm on" if llm_enabled else "/llm off"
                response = handle_command(context, cmd)
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            model_name = st.text_input(
                "Model AI",
                value=context.llm_model,
                key="model_input",
            )
            if model_name and model_name != context.llm_model:
                response = handle_command(context, f"/model {model_name}")
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            voice_enabled = st.checkbox(
                "Hlasová odpověď",
                value=context.voice_enabled,
                key="voice_toggle",
            )
            if voice_enabled != context.voice_enabled:
                cmd = "/voice on" if voice_enabled else "/voice off"
                response = handle_command(context, cmd)
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='ios-section-title'>Studijní nastavení</div>", unsafe_allow_html=True)
            st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("Subject", value=context.subject or "", key="subject_input")
                if subject and subject != (context.subject or ""):
                    response = handle_command(context, f"/subject {subject}")
                    st.session_state.chat_history.append(("system", response))
                    st.session_state.last_response = response

            with col2:
                level = st.text_input("Level", value=context.level or "", key="level_input")
                if level and level != (context.level or ""):
                    response = handle_command(context, f"/level {level}")
                    st.session_state.chat_history.append(("system", response))
                    st.session_state.last_response = response

            topic = st.text_area("Topic/Theme", value=context.topic or "", key="topic_input", height=80)
            if topic and topic != (context.topic or ""):
                response = handle_command(context, f"/topic {topic}")
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.subheader("Upload Files")
            uploaded_file = st.file_uploader(
                "Upload script/textbook (PDF, DOCX, TXT):",
                type=["pdf", "docx", "txt"],
                key="file_uploader"
            )
            
            if uploaded_file is not None:
                uploads_dir = Path(__file__).resolve().parent / "uploads"
                uploads_dir.mkdir(parents=True, exist_ok=True)
                saved_path = uploads_dir / uploaded_file.name
                saved_path.write_bytes(uploaded_file.getbuffer())

                try:
                    chunks = ingest_file(saved_path, source_label=uploaded_file.name)
                    if chunks:
                        context.sources.extend(chunks)
                        msg = f"✅ Uploaded {uploaded_file.name}: {len(chunks)} chunks ingested"
                        st.session_state.chat_history.append(("system", msg))
                        st.session_state.last_response = msg
                        st.success(msg)
                    else:
                        msg = "❌ No text found in file"
                        st.session_state.chat_history.append(("system", msg))
                        st.error(msg)
                except Exception as e:
                    msg = f"❌ Error: {str(e)}"
                    st.session_state.chat_history.append(("system", msg))
                    st.error(msg)
            
            # Allow ingesting files already present in the workspace `uploads/` folder
            uploads_dir = Path(__file__).resolve().parent / "uploads"
            uploads_list = []
            if uploads_dir.exists():
                uploads_list = [f.name for f in sorted(uploads_dir.iterdir()) if f.is_file()]

            if uploads_list:
                st.subheader("Repository uploads")
                selected = st.selectbox("Select file from uploads:", uploads_list, key="uploads_select")

                # Controls for lesson generation and export
                total_questions = st.slider(
                    "Total questions:",
                    min_value=10,
                    max_value=60,
                    value=30,
                    step=1,
                    key="total_questions",
                )
                preview_len = st.slider(
                    "Preview char limit:",
                    min_value=200,
                    max_value=800,
                    value=300,
                    step=10,
                    key="preview_len",
                )
                export_fmt = st.radio("Export format:", ["txt", "json", "csv"], index=0, key="export_fmt")

                col_a, col_b = st.columns([2,1])
                with col_a:
                    if st.button("Ingest selected file"):
                        sel_path = uploads_dir / selected
                        try:
                            chunks2 = ingest_file(sel_path, source_label=sel_path.name)
                            if chunks2:
                                context.sources.extend(chunks2)
                                msg2 = f"✅ Ingested {selected}: {len(chunks2)} chunks"
                                st.session_state.chat_history.append(("system", msg2))
                                st.session_state.last_response = msg2
                                st.success(msg2)
                            else:
                                msg2 = "❌ No text found in file"
                                st.session_state.chat_history.append(("system", msg2))
                                st.error(msg2)
                        except Exception as e:
                            msg2 = f"❌ Error: {str(e)}"
                            st.session_state.chat_history.append(("system", msg2))
                            st.error(msg2)
                with col_b:
                    if st.button("Generate lesson from selected"):
                        sel_path = uploads_dir / selected
                        try:
                            chunks2 = ingest_file(sel_path, source_label=sel_path.name)
                            query = _build_retrieval_query(context, st.session_state.search_query)
                            retrieved = retrieve_chunks(chunks2, query, limit=12) if query else chunks2[:12]
                            cited = [_with_citation_prefix(chunk) for chunk in retrieved]
                            lesson, analysis = generate_lesson_from_sources(
                                cited,
                                subject=context.subject or "ekonomie",
                                level=context.level or "zakladni",
                                strictness=context.engine.strictness,
                                n_total=int(total_questions),
                                preview_len=min(250, int(preview_len)),
                                return_meta=True,
                            )
                            # save lesson in chosen format
                            base_name = f"lesson_{selected}"
                            if export_fmt == "txt":
                                lesson_file = uploads_dir / f"{base_name}.txt"
                                lesson_file.write_text("\n\n".join(lesson), encoding="utf-8")
                                payload = None
                            elif export_fmt == "json":
                                lesson_file = uploads_dir / f"{base_name}.json"
                                lesson_file.write_text(json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")
                                payload = json.dumps(lesson, ensure_ascii=False).encode("utf-8")
                            else:  # csv
                                lesson_file = uploads_dir / f"{base_name}.csv"
                                with lesson_file.open("w", encoding="utf-8", newline="") as fh:
                                    writer = csv.writer(fh)
                                    for row in lesson:
                                        writer.writerow([row])
                                payload = lesson_file.read_bytes()

                            msg3 = f"✅ Generated lesson ({len(lesson)} items) and saved to {lesson_file.name}"
                            st.session_state.chat_history.append(("system", msg3))
                            st.session_state.last_response = msg3
                            st.success(msg3)
                            if analysis.topics:
                                topics_label = ", ".join(analysis.topics[:5])
                                st.write(f"Top topics: {topics_label}")
                            st.write(f"Explicit questions: {len(analysis.explicit_questions)}")
                            st.write(f"Final lesson count: {len(lesson)}")
                            # display preview truncated to preview_len
                            st.subheader("Generated lesson preview")
                            for i, it in enumerate(lesson[:20], 1):
                                display = it if len(it) <= int(preview_len) else it[: int(preview_len)] + "..."
                                st.write(f"{i}. {display}")

                            # provide download button for JSON/CSV or TXT
                            try:
                                if export_fmt == "txt":
                                    with lesson_file.open("rb") as fh:
                                        data = fh.read()
                                    st.download_button("Download lesson (txt)", data, file_name=lesson_file.name)
                                elif export_fmt == "json":
                                    st.download_button("Download lesson (json)", payload, file_name=lesson_file.name)
                                else:
                                    st.download_button("Download lesson (csv)", payload, file_name=lesson_file.name)
                            except Exception:
                                pass
                        except Exception as e:
                            msg3 = f"❌ Error generating lesson: {str(e)}"
                            st.session_state.chat_history.append(("system", msg3))
                            st.error(msg3)

                # Extra management actions
                st.divider()
                if st.button("Clear loaded sources"):
                    context.sources.clear()
                    st.session_state.active_context_chunks = []
                    st.session_state.search_results = []
                    st.success("Cleared loaded sources")
                    st.rerun()

                # Manage saved lessons
                lesson_files = [f.name for f in uploads_dir.iterdir() if f.is_file() and f.name.startswith("lesson_")]
                if lesson_files:
                    st.subheader("Saved lessons")
                    sel_les = st.selectbox("Select lesson to delete:", lesson_files, key="lesson_del_select")
                    if st.button("Delete selected lesson"):
                        try:
                            (uploads_dir / sel_les).unlink()
                            st.success(f"Deleted {sel_les}")
                        except Exception as e:
                            st.error(f"Error deleting: {e}")

            st.info(f"📄 {len(context.sources)} chunks loaded" if context.sources else "📄 No files loaded")
        
        with tab3:
            st.subheader("Lesson History")
            memory = load_memory(MEMORY_PATH)
            if memory.lesson_history:
                for i, record in enumerate(reversed(memory.lesson_history[-5:])):  # Last 5
                    st.write(
                        f"**{i+1}.** {record.timestamp}\n"
                        f"Subject: {record.subject or 'N/A'} | "
                        f"Errors: {record.errors} | "
                        f"Peak: {record.strictness_peak}"
                    )
            else:
                st.write("No lessons yet")
    
    # Main chat area
    st.subheader("Lesson Interface")
    
    # Display current state
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**State**: {format_state_display(context)}")
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()

    st.markdown("<div class='ios-section-title'>Vyhledávání v materiálech</div>", unsafe_allow_html=True)
    st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
    search_col, button_col = st.columns([3, 1])
    with search_col:
        search_query = st.text_input(
            "Hledej v PDF / skriptech",
            value=st.session_state.search_query,
            key="search_query_input",
        )
    with button_col:
        search_clicked = st.button("Search", use_container_width=True)
    if search_clicked:
        st.session_state.search_query = search_query
        results = []
        if search_query.strip():
            results = retrieve_chunks(context.sources, search_query, limit=5)
        st.session_state.search_results = results

    if st.session_state.search_results:
        st.markdown("**Top výsledky**")
        for item in st.session_state.search_results:
            page = item.page if item.page is not None else 1
            snippet = _clip_text(item.text, 250)
            st.markdown(
                f"<div class='ios-search-result'>"
                f"<div><strong>{item.source}</strong> · str. {page}</div>"
                f"<div>{snippet}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        if st.button("Použít jako kontext"):
            st.session_state.active_context_chunks = list(st.session_state.search_results)
            st.success("Vybrané chunky jsou aktivní kontext.")
    else:
        st.caption("Zatím žádné výsledky. Nahraj dokument a spusť hledání.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat history
    st.subheader("Conversation")
    chat_container = st.container(border=True)
    
    with chat_container:
        for role, message in st.session_state.chat_history:
            if role == "user":
                st.write(f"**You**: {message}")
            else:
                st.write(f"**Klara**: {message}")
    
    # Command input
    st.subheader("Input & Response")
    
    # Determine placeholder text based on context
    if context.session.last_question:
        placeholder = "Type your answer here..."
        help_text = "📝 Answer the question above"
    else:
        placeholder = "Type command (e.g., /help, /start) or text"
        help_text = "💬 Enter a command or text"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input(
            help_text,
            placeholder=placeholder,
            key="command_input"
        )
    with col2:
        submit = st.button("Send", use_container_width=True)
    
    if submit and user_input:
        # If there's a pending question, treat input as answer
        if context.session.last_question:
            response = handle_command(context, f"/answer {user_input}")
        else:
            # Otherwise treat as command
            response = handle_command(context, user_input)
        
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("system", response))
        st.session_state.last_response = response
        st.rerun()
    
    # Quick action buttons
    st.subheader("Quick Actions")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📖 Start"):
            response = handle_command(context, "/start")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    
    with col2:
        if st.button("❓ Ask"):
            if context.sources:
                if st.session_state.active_context_chunks:
                    retrieved = list(st.session_state.active_context_chunks)
                else:
                    retrieved = _retrieve_context_chunks(context, st.session_state.search_query, limit=5)
                    st.session_state.active_context_chunks = list(retrieved)
                cited = [_with_citation_prefix(chunk) for chunk in retrieved]
                response = _generate_question_from_context(context, cited)
                st.session_state.chat_history.append(("system", response))
            else:
                response = handle_command(context, "/ask")
                st.session_state.chat_history.append(("system", response))
            st.rerun()
    
    with col3:
        if st.button("✅ OK"):
            response = handle_command(context, "/ok")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    
    with col4:
        if st.button("❌ Fail"):
            response = handle_command(context, "/fail")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    
    with col5:
        if st.button("🏁 End"):
            response = handle_command(context, "/end")
            st.session_state.chat_history.append(("system", response))
            st.rerun()
    
    # Assistant mode todos
    if context.mode == "assistant":
        st.divider()
        st.subheader("📝 Todos (Assistant Mode)")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            todo_text = st.text_input("Add new todo:", key="todo_input")
        with col2:
            if st.button("Add", use_container_width=True):
                if todo_text:
                    response = handle_command(context, f"/todo add {todo_text}")
                    st.session_state.chat_history.append(("system", response))
                    st.rerun()
        
        memory = load_memory(MEMORY_PATH)
        if memory.todos:
            for i, todo in enumerate(memory.todos, 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{i}. {todo}")
                with col2:
                    if st.button("✓", key=f"todo_{i}"):
                        response = handle_command(context, f"/todo done {i}")
                        st.session_state.chat_history.append(("system", response))
                        st.rerun()
        else:
            st.info("No todos yet")
    
    # Display last response
    if st.session_state.last_response:
        st.divider()
        with st.container(border=True):
            st.info(st.session_state.last_response)


if __name__ == "__main__":
    main()
