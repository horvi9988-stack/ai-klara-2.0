"""Klara AI - Deployment & Setup Guide."""

# 🚀 Klara AI - Deployment Guide

## System Requirements

- **Python 3.12+**
- **pip** (Python package manager)
- **Optional: Ollama** (for local LLM support)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/horvi9988-stack/ai-klara-2.0.git
cd ai-klara-2.0
```

### 2. Create Virtual Environment (Recommended)

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The `requirements.txt` includes:
- `streamlit` - For GUI
- `pyttsx3`, `faster-whisper` - For voice
- `pypdf`, `python-docx` - For file upload
- `rapidfuzz` - For fuzzy matching

---

## Running the Application

### Option A: Web GUI (Recommended) 🎉

```bash
streamlit run streamlit_app.py
```

**Output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://10.x.x.x:8501
```

Open the URL in your browser. The app is ready to use!

### Option B: CLI (Terminal)

```bash
python main.py
```

Use `/help` to see available commands.

---

## Setting Up Local LLM (Optional)

For AI-powered questions without internet:

### 1. Install Ollama

Download from: https://ollama.com

### 2. Start Ollama Service

```bash
ollama serve
```

### 3. Pull a Model (in another terminal)

```bash
ollama pull llama2        # ~4GB
# OR
ollama pull neural-chat   # ~5GB  (recommended for Czech)
# OR
ollama pull mistral       # ~5GB  (faster)
```

### 4. Enable in Klara GUI

1. Click Settings → LLM Settings
2. Check "Enable LLM"
3. In command line: `/model llama2` (or your chosen model)

---

## Uploading Learning Materials

### In GUI:

1. Left sidebar → **Upload Tab**
2. Click "Upload script/textbook"
3. Select file: PDF, DOCX, or TXT
4. File is automatically processed

### Supported Formats:
- **PDF** - Textbooks, papers (requires `pypdf`)
- **DOCX** - Word documents (requires `python-docx`)
- **TXT** - Plain text files
- **MD** - Markdown (treated as text)

### Example:
```
- Upload math_tutorial.pdf
- Upload english_vocabulary.docx
- Upload physics_notes.txt
```

When you ask questions, content from these files becomes context for questions.

---

## Configuration Files

### `.streamlit/config.toml`
Streamlit settings (theme, logger level, etc.)

### `app/prompts/klara.txt`
Klara's persona and tone instructions. Edit to customize her personality.

### `app/storage/student_memory.json`
Stores:
- Lesson history
- User preferences
- Custom subjects
- Todos
- Weakness statistics

Deleted automatically on `/end` if desired.

---

## Directory Structure

```
ai-klara-2.0/
├── streamlit_app.py         # GUI entry point
├── main.py                  # CLI entry point
├── requirements.txt         # Dependencies
├── GUI_GUIDE.md            # GUI user manual
├── DEPLOYMENT.md           # This file
│
├── app/
│   ├── cli.py              # CLI commands handler
│   ├── core/               # Core logic
│   │   ├── evaluator.py    # Answer evaluation
│   │   ├── levels.py       # Difficulty levels
│   │   ├── mock_llm.py     # Fallback responses
│   │   ├── question_engine.py
│   │   ├── session.py
│   │   ├── state_machine.py
│   │   ├── subjects.py
│   │   └── voice.py
│   ├── llm/
│   │   └── ollama_client.py # Ollama integration
│   ├── storage/
│   │   └── memory.py        # Persistence layer
│   └── prompts/
│       └── klara.txt        # Persona definition
│
├── tests/                   # Unit tests
└── .streamlit/
    └── config.toml         # Streamlit config
```

---

## Running Tests

```bash
python -m unittest
```

Expected output:
```
Ran 34 tests in 0.003s
OK
```

---

## Troubleshooting

### Streamlit won't start
```bash
# Try a different port
streamlit run streamlit_app.py --server.port 8502
```

### File upload fails
- Check file size (< 200MB recommended)
- Ensure write permissions to `app/storage/`
- For PDF/DOCX, verify `pypdf` and `python-docx` installed

### LLM not working
```bash
# Check if Ollama is running
curl http://localhost:11434/api/models

# Pull a model
ollama pull neural-chat
```

### Settings not persisting
- Check `app/storage/student_memory.json` exists
- Ensure write permissions
- Try deleting the file and reopening app (recreates with defaults)

---

## Running on a Different Machine

1. **Install Python 3.12+**
2. **Clone repo** and create venv
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Run Streamlit**: `streamlit run streamlit_app.py`
5. **Open browser**: `http://localhost:8501`

That's it! No server needed. Everything runs locally. ✨

---

## Advanced: Custom Domain/Port

```bash
# Run on specific port
streamlit run streamlit_app.py --server.port 8080

# Run on all network interfaces (accessible from other machines)
streamlit run streamlit_app.py --server.address 0.0.0.0

# Disable browser auto-open
streamlit run streamlit_app.py --logger.level=error --client.showErrorDetails=false
```

---

## Features Overview

✅ **CLI & GUI modes** - Choose what works for you
✅ **File upload** - Add textbooks and scripts
✅ **Local LLM** - No internet needed (with Ollama)
✅ **Voice support** - Input/output with microphone
✅ **Persistent memory** - Settings saved automatically
✅ **Multiple users** - Independent lesson histories
✅ **Custom subjects** - Add your own teaching areas
✅ **Todo manager** - In assistant mode
✅ **Weakness tracking** - Identifies struggling topics

---

## Support

For issues or questions:
- Check [GUI_GUIDE.md](GUI_GUIDE.md) for user manual
- Check [README.md](README.md) for quick start
- Review [CODEX.md](CODEX.md) for design notes

Enjoy teaching and learning with Klara! 🎓✨
