from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage" / "sources"


@dataclass
class SourceChunk:
    text: str
    source: str


def ingest_file(path: str) -> tuple[str, int]:
    source_path = Path(path).expanduser()
    if not source_path.exists():
        raise ValueError(f"File not found: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise ValueError("Unsupported file type. Use .txt or .md only.")
    text = source_path.read_text(encoding="utf-8", errors="ignore")
    source_id = uuid.uuid4().hex
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    target_path = STORAGE_DIR / f"{source_id}.txt"
    target_path.write_text(text, encoding="utf-8")
    return source_id, len(text)


def list_sources() -> list[dict[str, object]]:
    if not STORAGE_DIR.exists():
        return []
    entries: list[dict[str, object]] = []
    for source_path in sorted(STORAGE_DIR.glob("*.txt")):
        source_id = source_path.stem
        try:
            text = source_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        entries.append(
            {
                "id": source_id,
                "path": str(source_path),
                "chars_count": len(text),
            }
        )
    return entries


def load_source_texts(source_ids: list[str]) -> list[str]:
    texts: list[str] = []
    for source_id in source_ids:
        source_path = STORAGE_DIR / f"{source_id}.txt"
        if not source_path.exists():
            continue
        try:
            text = source_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if text:
            texts.append(text)
    return texts


def build_source_chunks(
    source_ids: list[str],
    *,
    chunk_size: int = 400,
    overlap: int = 40,
) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    for source_id in source_ids:
        source_path = STORAGE_DIR / f"{source_id}.txt"
        if not source_path.exists():
            continue
        try:
            text = source_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        chunks.extend(
            _chunk_text(
                text,
                source=source_id,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )
    return chunks


def suggest_topic(source_ids: list[str]) -> str | None:
    texts = load_source_texts(source_ids)
    if not texts:
        return None
    tokens: list[str] = []
    for text in texts:
        tokens.extend(_tokenize(text))
    if not tokens:
        return None
    stopwords = {
        "that",
        "this",
        "with",
        "from",
        "have",
        "your",
        "about",
        "there",
        "their",
        "these",
        "those",
        "which",
        "would",
        "could",
        "should",
        "also",
        "into",
        "when",
        "what",
        "where",
        "while",
        "they",
        "them",
        "then",
        "than",
        "some",
        "such",
        "more",
        "most",
        "been",
        "were",
        "will",
        "able",
        "over",
        "under",
        "using",
        "used",
    }
    filtered = [token for token in tokens if token not in stopwords]
    if not filtered:
        return None
    most_common = Counter(filtered).most_common(1)
    if not most_common:
        return None
    return most_common[0][0]


def retrieve_chunks(chunks: list[SourceChunk], query: str, *, limit: int = 3) -> list[SourceChunk]:
    if not chunks:
        return []
    tokens = _tokenize(query)
    if not tokens:
        return chunks[:limit]
    scored: list[tuple[int, SourceChunk]] = []
    for chunk in chunks:
        chunk_text = chunk.text.lower()
        score = sum(1 for token in tokens if token in chunk_text)
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for score, chunk in scored if score > 0][:limit] or chunks[:limit]


def _chunk_text(text: str, *, source: str, chunk_size: int, overlap: int) -> list[SourceChunk]:
    words = text.split()
    if not words:
        return []
    chunks: list[SourceChunk] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        segment = " ".join(words[start : start + chunk_size]).strip()
        if segment:
            chunks.append(SourceChunk(text=segment, source=source))
    return chunks


def _tokenize(text: str) -> list[str]:
    tokens = [token for token in re.split(r"\W+", text.lower()) if len(token) > 2]
    return tokens
