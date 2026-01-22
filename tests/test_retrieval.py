from app.core.local_sources import SourceChunk
from app.core.retrieval import search_chunks


def test_retrieval_returns_relevant_chunk():
    chunks = [
        SourceChunk(id="test-p1-1", source_file="test", page_num=1, text="apple banana fruit salad"),
        SourceChunk(id="test-p1-2", source_file="test", page_num=1, text="car engine fuel and torque"),
        SourceChunk(id="test-p1-3", source_file="test", page_num=1, text="banana smoothie recipe with milk"),
    ]
    results = search_chunks("banana recipe", chunks, top_k=1)
    assert results
    assert "smoothie" in results[0].text
