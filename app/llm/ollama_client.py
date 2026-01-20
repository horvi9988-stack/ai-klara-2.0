from __future__ import annotations

"""Minimal Ollama client wrapper."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1"


def generate(prompt: str, *, model: str = DEFAULT_MODEL, timeout_s: int = 30) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    data = json.dumps(payload).encode("utf-8")
    request = Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
        parsed = json.loads(body)
        reply = str(parsed.get("response", "")).strip()
        if reply:
            return reply
        return "Ollama returned an empty response."
    except URLError:
        return "Ollama is not running. Start it with: ollama serve"
    except TimeoutError:
        return "Ollama request timed out. Try again."
    except Exception as exc:  # pragma: no cover - unexpected runtime error
        return f"Ollama error: {exc}"
