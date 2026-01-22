from app.core.local_sources import SourceChunk, retrieve_chunks
from app.core.retrieval import build_index, search


def test_retrieval_returns_relevant_chunk():
    chunks = [
        SourceChunk(text="apple banana fruit salad", source="test"),
        SourceChunk(text="car engine fuel and torque", source="test"),
        SourceChunk(text="banana smoothie recipe with milk", source="test"),
    ]
    index = build_index(chunks)
    results = search(index, "banana recipe", k=1)
    assert results
    assert "smoothie" in results[0].text


def test_retrieve_chunks_ranks_query_matches():
    chunks = [
        SourceChunk(text="alpha beta gamma", source="notes.txt"),
        SourceChunk(text="delta epsilon zeta", source="notes.txt"),
        SourceChunk(text="beta wins over delta", source="notes.txt"),
    ]
    results = retrieve_chunks(chunks, "beta", limit=1)
    assert results
    assert "beta" in results[0].text
