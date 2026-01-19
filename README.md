# ai-klara-2.0

Klara is a local CLI tutor. This repo runs fully offline with an optional local LLM
via Ollama and optional voice input/output.

## Quick start

```bash
python main.py
```

Use `/help` to see available commands.

## Local LLM with Ollama (free/local mode)

1. Install Ollama: https://ollama.com
2. Start the service:
   ```bash
   ollama serve
   ```
3. Pull a model (default is `llama3.1`):
   ```bash
   ollama pull llama3.1
   ```
4. In the app:
   ```
   /llm on
   /model llama3.1
   ```

The app does not auto-download models. If Ollama is not running, the app falls
back to rule-based questions.

## Local file ingest (txt/md/pdf/docx)

Load local documents and use them as question context:

```
/ingest /path/to/notes.md
/sources
/ask
```

For PDF or DOCX ingestion, install optional dependencies:

```bash
pip install pypdf python-docx
```

## Optional voice mode (push to talk)

Voice mode uses faster-whisper for transcription and a local TTS engine.

Install optional dependencies:

```bash
pip install faster-whisper sounddevice numpy pyttsx3
```

Enable voice mode and record 5 seconds of audio:

```
/voice on
/ptt
```

If a dependency is missing, the CLI prints a friendly install hint.

## Notes

- Default model: `llama3.1`
- All data stays local and in memory unless stored by the app.
