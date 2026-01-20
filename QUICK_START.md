# 🚀 Quick Start - Klara AI

## Installation & Run (5 minutes)

```bash
# 1. Install Python 3.12+ from python.org

# 2. Clone & setup
git clone https://github.com/horvi9988-stack/ai-klara-2.0.git
cd ai-klara-2.0
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run GUI (recommended!)
streamlit run streamlit_app.py

# 5. Browser opens automatically at http://localhost:8501 ✨
```

## GUI Features

### 📚 Teaching Mode
1. Set **Subject** (mathematics, english, history, etc.)
2. Set **Level** (zakladni, stredni, vysoka)
3. Set **Topic** (what to teach)
4. **📁 Upload PDF/DOCX** with materials
5. Click **Start** → **Ask** → **OK/Fail** → **End**

### 📝 Assistant Mode
1. Switch to **Mode: assistant**
2. Add todos in the section below
3. Check them off when done
4. Everything persists!

### 📁 File Upload
- Drag-and-drop PDF, DOCX, or TXT
- Questions use file content as context
- Upload multiple files together

## Commands (Type in Input Box)

```
/start              - Begin lesson
/ask                - Get question
/ok                 - Mark correct
/fail               - Mark incorrect  
/end                - Finish & save
/subject <name>     - Set subject
/level <name>       - Set level
/mode teacher       - Teaching mode
/mode assistant     - Todo mode
/todo add <text>    - Add todo
/todo list          - List todos
/help               - All commands
```

## CLI Mode (Alternative)

```bash
python main.py
```

Type `/help` for commands.

---

**Everything runs locally. No internet needed!** 🔒

For detailed guides:
- **GUI Guide**: [GUI_GUIDE.md](GUI_GUIDE.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Project Info**: [SUMMARY.md](SUMMARY.md)
