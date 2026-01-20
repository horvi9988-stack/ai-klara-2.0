"""Streamlit GUI for Klara AI Tutoring System."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.cli import CliContext, handle_command
from app.core.session import LessonSession
from app.core.state_machine import TeacherEngine
from app.llm.ollama_client import DEFAULT_MODEL
from app.storage.memory import load_memory, save_memory
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


def main() -> None:
    """Main Streamlit app."""
    init_session_state()
    context = st.session_state.context
    
    st.title("📚 Klara AI - Tutoring System")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        tab1, tab2, tab3 = st.tabs(["Settings", "Upload", "History"])
        
        with tab1:
            st.subheader("Mode")
            mode = st.radio(
                "Select mode:",
                ["teacher", "assistant"],
                index=0 if context.mode == "teacher" else 1,
                key="mode_selector"
            )
            if mode != context.mode:
                response = handle_command(context, f"/mode {mode}")
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            
            st.subheader("Subject & Level")
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("Subject:", value=context.subject or "", key="subject_input")
                if subject and subject != (context.subject or ""):
                    response = handle_command(context, f"/subject {subject}")
                    st.session_state.chat_history.append(("system", response))
                    st.session_state.last_response = response
            
            with col2:
                level = st.text_input("Level:", value=context.level or "", key="level_input")
                if level and level != (context.level or ""):
                    response = handle_command(context, f"/level {level}")
                    st.session_state.chat_history.append(("system", response))
                    st.session_state.last_response = response
            
            st.subheader("Topic")
            topic = st.text_area("Topic/Theme:", value=context.topic or "", key="topic_input", height=80)
            if topic and topic != (context.topic or ""):
                response = handle_command(context, f"/topic {topic}")
                st.session_state.chat_history.append(("system", response))
                st.session_state.last_response = response
            
            st.subheader("LLM Settings")
            llm_enabled = st.checkbox("Enable LLM", value=context.llm_enabled, key="llm_checkbox")
            if llm_enabled != context.llm_enabled:
                cmd = "/llm on" if llm_enabled else "/llm off"
                response = handle_command(context, cmd)
                st.session_state.chat_history.append(("system", response))
        
        with tab2:
            st.subheader("Upload Files")
            uploaded_file = st.file_uploader(
                "Upload script/textbook (PDF, DOCX, TXT):",
                type=["pdf", "docx", "txt"],
                key="file_uploader"
            )
            
            if uploaded_file is not None:
                # Save to temp file and ingest
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                
                try:
                    chunks = ingest_file(Path(tmp_path))
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
                finally:
                    Path(tmp_path).unlink()
            
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
