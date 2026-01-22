from __future__ import annotations

"""Local retrieval utilities with a lightweight BM25 implementation."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.local_sources import SourceChunk

TOKEN_RE = re.compile(r"[^a-z0-9]+")

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "your",
    "you",
    "are",
    "was",
    "were",
    "have",
    "has",
    "had",
    "not",
    "but",
    "into",
    "onto",
    "over",
    "under",
    "also",
}


@dataclass
class Index:
    chunks: list["SourceChunk"]
    tf: list[dict[str, int]]
    df: dict[str, int]
    doc_len: list[int]
    avgdl: float


def tokenize(text: str) -> list[str]:
    tokens = [t for t in TOKEN_RE.split(text.lower()) if len(t) > 2]
    return [t for t in tokens if t not in STOPWORDS]


def build_index(chunks: list["SourceChunk"]) -> Index:
    tf: list[dict[str, int]] = []
    df: Counter[str] = Counter()
    doc_len: list[int] = []
    for chunk in chunks:
        tokens = tokenize(chunk.text)
        counts = Counter(tokens)
        tf.append(dict(counts))
        doc_len.append(sum(counts.values()))
        for term in counts:
            df[term] += 1
    avgdl = sum(doc_len) / len(doc_len) if doc_len else 0.0
    return Index(chunks=chunks, tf=tf, df=dict(df), doc_len=doc_len, avgdl=avgdl)


def search(index: Index, query: str, *, k: int = 3) -> list["SourceChunk"]:
    if not index.chunks:
        return []
    tokens = tokenize(query)
    if not tokens:
        return index.chunks[:k]
    total_docs = len(index.chunks)
    scores: list[tuple[float, int]] = []
    avgdl = index.avgdl or 1.0
    k1 = 1.5
    b = 0.75
    for doc_id, tf in enumerate(index.tf):
        score = 0.0
        doc_length = index.doc_len[doc_id] if doc_id < len(index.doc_len) else 0
        for term in tokens:
            freq = tf.get(term, 0)
            if not freq:
                continue
            doc_freq = index.df.get(term, 0)
            idf = math.log(1.0 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
            denom = freq + k1 * (1 - b + b * (doc_length / avgdl))
            score += idf * (freq * (k1 + 1)) / denom
        scores.append((score, doc_id))
    scores.sort(reverse=True)
    if not scores or scores[0][0] <= 0:
        return index.chunks[:k]
    return [index.chunks[doc_id] for score, doc_id in scores[:k] if score > 0]


def search_chunks(query: str, chunks: list["SourceChunk"], top_k: int = 3) -> list["SourceChunk"]:
    if not chunks:
        return []
    index = build_index(chunks)
    return search(index, query, k=top_k)


def index_to_cache(index: Index) -> dict[str, object]:
    return {
        "version": 1,
        "df": index.df,
        "doc_len": index.doc_len,
        "tf": index.tf,
    }


def index_from_cache(data: dict[str, object], chunks: list["SourceChunk"]) -> Index | None:
    if data.get("version") != 1:
        return None
    tf_raw = data.get("tf")
    df_raw = data.get("df")
    doc_len = data.get("doc_len")
    if not isinstance(tf_raw, list) or not isinstance(df_raw, dict) or not isinstance(doc_len, list):
        return None
    if len(tf_raw) != len(chunks) or len(doc_len) != len(chunks):
        return None
    tf = []
    for item in tf_raw:
        if not isinstance(item, dict):
            return None
        tf.append({str(k): int(v) for k, v in item.items()})
    df = {str(k): int(v) for k, v in df_raw.items()}
    avgdl = sum(int(length) for length in doc_len) / len(doc_len) if doc_len else 0.0
    doc_len_int = [int(length) for length in doc_len]
    return Index(chunks=chunks, tf=tf, df=df, doc_len=doc_len_int, avgdl=avgdl)
