from app.core.local_sources import SourceChunk
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
