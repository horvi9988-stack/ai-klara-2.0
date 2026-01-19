from __future__ import annotations

import importlib
import importlib.util

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_RECORD_SECONDS = 5


def voice_dependency_message() -> str | None:
    missing = _missing_voice_deps()
    if missing:
        joined = ", ".join(missing)
        pip_install = " ".join(missing)
        return (
            "Missing optional voice dependencies: "
            f"{joined}. Install with: pip install {pip_install}"
        )
    return None


def tts_dependency_message() -> str | None:
    if importlib.util.find_spec("pyttsx3") is None:
        return "Missing optional TTS dependency: pyttsx3. Install with: pip install pyttsx3"
    return None


def record_and_transcribe(
    *,
    seconds: int = DEFAULT_RECORD_SECONDS,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> tuple[str | None, str | None]:
    message = voice_dependency_message()
    if message:
        return None, message
    audio, used_rate = _record_audio(seconds=seconds, sample_rate=sample_rate)
    transcript = _transcribe_audio(audio, sample_rate=used_rate)
    if not transcript.strip():
        return None, "No speech detected."
    return transcript.strip(), None


def speak_text(text: str) -> str | None:
    message = tts_dependency_message()
    if message:
        return message
    pyttsx3 = importlib.import_module("pyttsx3")
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return None


def _missing_voice_deps() -> list[str]:
    missing = []
    if importlib.util.find_spec("sounddevice") is None:
        missing.append("sounddevice")
    if importlib.util.find_spec("numpy") is None:
        missing.append("numpy")
    if importlib.util.find_spec("faster_whisper") is None:
        missing.append("faster-whisper")
    return missing


def _record_audio(*, seconds: int, sample_rate: int):
    sounddevice = importlib.import_module("sounddevice")
    numpy = importlib.import_module("numpy")
    frames = int(seconds * sample_rate)
    audio = sounddevice.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sounddevice.wait()
    return numpy.squeeze(audio), sample_rate


def _transcribe_audio(audio, *, sample_rate: int) -> str:
    faster_whisper = importlib.import_module("faster_whisper")
    model = faster_whisper.WhisperModel("base", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(audio, beam_size=5, sample_rate=sample_rate)
    parts = [segment.text.strip() for segment in segments if segment.text]
    return " ".join(parts)
