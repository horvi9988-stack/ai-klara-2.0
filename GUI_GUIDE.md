"""Streamlit GUI User Guide for Klara AI Tutoring System."""

# 📚 Klara GUI - User Guide

## Starting the GUI

```bash
streamlit run streamlit_app.py
```

The app automatically opens in your browser. If not, go to: **http://localhost:8501**

---

## Interface Layout

### Left Sidebar - Configuration

Three tabs for easy setup:

#### 1. **Settings Tab**
- **Mode**: Switch between "teacher" (tutoring) and "assistant" (todo manager)
- **Subject & Level**: Set what you're teaching/learning
- **Topic/Theme**: Describe the lesson subject
- **LLM Settings**: Enable/disable AI-powered questions

#### 2. **Upload Tab** 🆕
- **Upload Files**: Add scripts, textbooks, or notes (PDF, DOCX, TXT)
- Shows how many chunks are loaded
- Uploaded files become context for questions

#### 3. **History Tab**
- View last 5 lessons with timestamps
- See errors, strictness peak per lesson

### Main Area - Lesson Interface

#### **Current State**
Shows: Subject, Level, Topic, Mode, Strictness, Section, Errors, LLM Status, Voice Status

#### **Conversation**
- Displays all messages between you and Klara
- Shows your commands and Klara's responses

#### **Command Input**
- Enter commands or text
- Type `/help` to see all available commands
- Hit "Send" to execute

#### **Quick Action Buttons**
- 📖 **Start**: Begin a new lesson
- ❓ **Ask**: Get a question
- ✅ **OK**: Mark answer as correct
- ❌ **Fail**: Mark answer as incorrect
- 🏁 **End**: Finish lesson and save

#### **Todos (Assistant Mode Only)**
- Add new todos
- Check off completed items
- Todos persist across sessions

---

## Workflow Example

### 1. Teacher Mode - Give a Lesson

```
1. Click left sidebar → Settings
2. Set Mode: "teacher"
3. Set Subject: "mathematics"
4. Set Level: "zakladni" (basic)
5. Set Topic: "addition" or upload a PDF with examples
6. Click "Start" button
7. Click "Ask" to get a question
8. Student answers in command input (or you read their answer)
9. Click "OK" if correct, "Fail" if not
10. Repeat steps 7-9
11. Click "End" to finish and save
```

### 2. Assistant Mode - Manage Todos

```
1. Click left sidebar → Settings
2. Set Mode: "assistant"
3. Scroll down to "Todos (Assistant Mode)"
4. Add tasks you want to track
5. Check off completed items
6. Todos save automatically
```

### 3. Upload Teaching Materials

```
1. Click left sidebar → Upload tab
2. Click "Upload script/textbook"
3. Select a PDF, DOCX, or TXT file
4. File is processed and chunks appear at bottom
5. When you ask questions, content is used as context
```

---

## Available Commands

Type in the **Command Input** box and hit "Send":

```
/help                  - Show all commands
/start                 - Begin a lesson
/subject <name>        - Set subject
/subject add <name>    - Add custom subject
/level <name>          - Set difficulty level
/topic <text>          - Set lesson topic
/mode teacher|assistant - Switch mode
/todo add <text>       - Add todo (assistant mode)
/todo list             - List todos (assistant mode)
/todo done <index>     - Mark todo done (assistant mode)
/ask                   - Get a question
/answer <text>         - Submit an answer
/ok                    - Correct answer
/fail                  - Incorrect answer
/next                  - Get next question
/repeat                - Show last question again
/quiz <n>              - Get n questions
/weak                  - Show weakest topics
/end                   - End lesson
/status                - Show current state
```

---

## Settings Persistence

All settings are automatically saved:
- Subject, Level, Topic
- Mode (teacher/assistant)
- LLM enabled/disabled
- Todos (in assistant mode)
- Upload file context

When you close and reopen the app, your settings are restored! ✨

---

## Tips & Tricks

- 📁 **Upload multiple files** at once by uploading again
- 📊 **Check History** to see your progress over time
- 🎯 **Use /weak** to identify struggling areas
- 🤖 **Enable LLM** for more varied, AI-generated questions
- ✍️ **Write detailed topics** - Klara uses this for better questions
- 🔄 **Refresh** button in the main area reloads the UI

---

## Troubleshooting

**GUI not opening?**
- Make sure port 8501 is not in use
- Try: `streamlit run streamlit_app.py --server.port 8502`

**File upload not working?**
- Check file size (should be < 200MB)
- Try supported formats: PDF, DOCX, TXT

**Settings not saving?**
- Ensure you have write permissions to `app/storage/student_memory.json`
- Try closing and reopening the browser

**LLM not responding?**
- Make sure Ollama is running: `ollama serve`
- Check: `/llm on` then `/ask`

---

Enjoy learning with Klara! 📚✨
