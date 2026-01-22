from __future__ import annotations

"""Local document ingestion and simple chunk retrieval."""

import hashlib
import importlib
import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.core import retrieval


@dataclass
class SourceChunk:
    text: str
    source: str
    page: int | None = None
    source_path: str | None = None


def ingest_file(
    path: Path,
    *,
    chunk_size: int = 700,
    overlap: int = 100,
    source_label: str | None = None,
) -> list[SourceChunk]:
    if not path.exists():
        raise ValueError(f"File not found: {path}")
    label = source_label or path.name
    source_path = str(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return _chunk_text(
            text,
            source=label,
            source_path=source_path,
            chunk_size=chunk_size,
            overlap=overlap,
        )
    if suffix == ".pdf":
        _ensure_dependency("pypdf", "pypdf")
        pdf = importlib.import_module("pypdf")
        try:
            reader = pdf.PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            # Fallback: some uploaded files may be plain text saved with .pdf extension
            # or malformed PDFs; try to read as text to still extract content.
            pages = [path.read_text(encoding="utf-8", errors="ignore")]
        chunks: list[SourceChunk] = []
        for page_number, page_text in enumerate(pages, start=1):
            chunks.extend(
                _chunk_text(
                    page_text,
                    source=label,
                    source_path=source_path,
                    page=page_number,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
            )
        return chunks
    if suffix == ".docx":
        _ensure_dependency("docx", "python-docx")
        docx = importlib.import_module("docx")
        document = docx.Document(str(path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        text = "\n".join(paragraphs)
        return _chunk_text(
            text,
            source=label,
            source_path=source_path,
            chunk_size=chunk_size,
            overlap=overlap,
        )
    raise ValueError("Unsupported file type. Use txt, md, pdf, or docx.")


def retrieve_chunks(chunks: list[SourceChunk], query: str, *, limit: int = 3) -> list[SourceChunk]:
    if not chunks:
        return []
    cache_context = _get_cache_context(chunks)
    if cache_context and cache_context.cache_path.exists():
        cached = _load_cached_index(cache_context, chunks)
        if cached:
            return retrieval.search(cached, query, k=limit)
    index = retrieval.build_index(chunks)
    results = retrieval.search(index, query, k=limit)
    if cache_context:
        _save_cached_index(cache_context, index)
    return results


def _ensure_dependency(module_name: str, package_name: str) -> None:
    if importlib.util.find_spec(module_name) is None:
        raise ValueError(
            "Missing optional dependency. Install with: "
            f"pip install {package_name}"
        )


def _chunk_text(
    text: str,
    *,
    source: str,
    source_path: str | None,
    chunk_size: int,
    overlap: int,
    page: int | None = None,
) -> list[SourceChunk]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[SourceChunk] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(normalized), step):
        segment = normalized[start : start + chunk_size].strip()
        if segment:
            chunks.append(
                SourceChunk(
                    text=segment,
                    source=source,
                    page=page,
                    source_path=source_path,
                )
            )
    return chunks


def _tokenize(text: str) -> list[str]:
    tokens = [token for token in re.split(r"\W+", text.lower()) if len(token) > 2]
    return tokens


def _simple_retrieve(chunks: list[SourceChunk], query: str, *, limit: int) -> list[SourceChunk]:
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


def _get_cache_context(chunks: list[SourceChunk]) -> _CacheContext | None:
    if not chunks:
        return None
    chunk_hashes = [_hash_text(chunk.text) for chunk in chunks]
    cache_dir = _index_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    source_labels = [chunk.source for chunk in chunks]
    source_paths = [chunk.source_path or "" for chunk in chunks]
    chunk_list_hash = _hash_text("".join(chunk_hashes) + "|" + "|".join(source_labels + source_paths))
    cache_path = cache_dir / f"{chunk_list_hash}.json"
    return _CacheContext(
        chunk_hashes=chunk_hashes,
        source_labels=source_labels,
        source_paths=source_paths,
        cache_path=cache_path,
    )


def _load_cached_index(context: _CacheContext, chunks: list[SourceChunk]) -> retrieval.Index | None:
    try:
        payload = json.loads(context.cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("chunk_hashes") != context.chunk_hashes:
        return None
    if payload.get("source_labels") != context.source_labels:
        return None
    if payload.get("source_paths") != context.source_paths:
        return None
    data = payload.get("index")
    if not isinstance(data, dict):
        return None
    return retrieval.index_from_cache(data, chunks)


def _save_cached_index(context: _CacheContext, index: retrieval.Index) -> None:
    payload = {
        "chunk_hashes": context.chunk_hashes,
        "source_labels": context.source_labels,
        "source_paths": context.source_paths,
        "index": retrieval.index_to_cache(index),
    }
    context.cache_path.write_text(json.dumps(payload), encoding="utf-8")


def _index_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "uploads" / ".index"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


@dataclass(frozen=True)
class _CacheContext:
    chunk_hashes: list[str]
    source_labels: list[str]
    source_paths: list[str]
    cache_path: Path
