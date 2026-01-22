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
    id: str
    source_file: str
    page_num: int
    text: str


def ingest_file(path: Path, *, chunk_size: int = 600, overlap: int = 100) -> list[SourceChunk]:
    if not path.exists():
        raise ValueError(f"File not found: {path}")
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return _chunk_text(text, source=str(path), page_num=1, chunk_size=chunk_size, overlap=overlap)
    if suffix == ".pdf":
        _ensure_dependency("pypdf", "pypdf")
        pdf = importlib.import_module("pypdf")
        try:
            reader = pdf.PdfReader(str(path))
            chunks: list[SourceChunk] = []
            for page_index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                chunks.extend(
                    _chunk_text(
                        page_text,
                        source=str(path),
                        page_num=page_index,
                        chunk_size=chunk_size,
                        overlap=overlap,
                    )
                )
            return chunks
        except Exception:
            # Fallback: some uploaded files may be plain text saved with .pdf extension
            # or malformed PDFs; try to read as text to still extract content.
            text = path.read_text(encoding="utf-8", errors="ignore")
            return _chunk_text(text, source=str(path), page_num=1, chunk_size=chunk_size, overlap=overlap)
    if suffix == ".docx":
        _ensure_dependency("docx", "python-docx")
        docx = importlib.import_module("docx")
        document = docx.Document(str(path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        text = "\n".join(paragraphs)
        return _chunk_text(text, source=str(path), page_num=1, chunk_size=chunk_size, overlap=overlap)
    raise ValueError("Unsupported file type. Use txt, md, pdf, or docx.")


def retrieve_chunks(chunks: list[SourceChunk], query: str, *, limit: int = 3) -> list[SourceChunk]:
    if not chunks:
        return []
    cache_context = _get_cache_context(chunks)
    if cache_context and cache_context.cache_path.exists():
        cached = _load_cached_index(cache_context, chunks)
        if cached:
            return retrieval.search(cached, query, k=limit)
    results = _simple_retrieve(chunks, query, limit=limit)
    if cache_context:
        index = retrieval.build_index(chunks)
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
    page_num: int,
    chunk_size: int,
    overlap: int,
) -> list[SourceChunk]:
    cleaned = text.replace("\n", " ").strip()
    if not cleaned:
        return []
    chunks: list[SourceChunk] = []
    step = max(1, chunk_size - overlap)
    source_name = Path(source).name
    for start in range(0, len(cleaned), step):
        segment = cleaned[start : start + chunk_size].strip()
        if segment:
            chunk_id = f"{source_name}-p{page_num}-{len(chunks) + 1}"
            chunks.append(
                SourceChunk(
                    id=chunk_id,
                    source_file=source_name,
                    page_num=page_num,
                    text=segment,
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
    source = chunks[0].source_file
    if any(chunk.source_file != source for chunk in chunks):
        return None
    source_path = Path(__file__).resolve().parents[2] / "uploads" / source
    if not source_path.exists():
        return None
    file_hash = _hash_file(source_path)
    chunk_hashes = [_hash_text(f"{chunk.id}:{chunk.page_num}:{chunk.text}") for chunk in chunks]
    cache_dir = _index_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    chunk_list_hash = _hash_text("".join(chunk_hashes))
    cache_path = cache_dir / f"{file_hash}_{chunk_list_hash}.json"
    return _CacheContext(
        source_path=source_path,
        file_hash=file_hash,
        chunk_hashes=chunk_hashes,
        cache_path=cache_path,
    )


def _load_cached_index(context: _CacheContext, chunks: list[SourceChunk]) -> retrieval.Index | None:
    try:
        payload = json.loads(context.cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("file_hash") != context.file_hash:
        return None
    if payload.get("chunk_hashes") != context.chunk_hashes:
        return None
    data = payload.get("index")
    if not isinstance(data, dict):
        return None
    return retrieval.index_from_cache(data, chunks)


def _save_cached_index(context: _CacheContext, index: retrieval.Index) -> None:
    payload = {
        "file_hash": context.file_hash,
        "chunk_hashes": context.chunk_hashes,
        "index": retrieval.index_to_cache(index),
    }
    context.cache_path.write_text(json.dumps(payload), encoding="utf-8")


def _index_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "uploads" / ".index"


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


@dataclass(frozen=True)
class _CacheContext:
    source_path: Path
    file_hash: str
    chunk_hashes: list[str]
    cache_path: Path
