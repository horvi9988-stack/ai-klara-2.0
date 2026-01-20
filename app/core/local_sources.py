from __future__ import annotations

"""Local document ingestion and simple chunk retrieval."""

import importlib
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceChunk:
    text: str
    source: str


def ingest_file(path: Path, *, chunk_size: int = 400, overlap: int = 40) -> list[SourceChunk]:
    if not path.exists():
        raise ValueError(f"File not found: {path}")
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return _chunk_text(text, source=str(path), chunk_size=chunk_size, overlap=overlap)
    if suffix == ".pdf":
        _ensure_dependency("pypdf", "pypdf")
        pdf = importlib.import_module("pypdf")
        reader = pdf.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
        return _chunk_text(text, source=str(path), chunk_size=chunk_size, overlap=overlap)
    if suffix == ".docx":
        _ensure_dependency("docx", "python-docx")
        docx = importlib.import_module("docx")
        document = docx.Document(str(path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        text = "\n".join(paragraphs)
        return _chunk_text(text, source=str(path), chunk_size=chunk_size, overlap=overlap)
    raise ValueError("Unsupported file type. Use txt, md, pdf, or docx.")


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


def _ensure_dependency(module_name: str, package_name: str) -> None:
    if importlib.util.find_spec(module_name) is None:
        raise ValueError(
            "Missing optional dependency. Install with: "
            f"pip install {package_name}"
        )


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
