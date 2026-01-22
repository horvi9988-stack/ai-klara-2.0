from app.core.local_sources import SourceChunk
from app.core.question_engine import generate_question


def test_generate_question_includes_source_citation():
    chunks = [
        SourceChunk(
            text="[Zdroj: economics.pdf, str. 2] Nabídka a poptávka tvoří základ trhu.",
            source="economics.pdf",
            page=2,
        )
    ]
    question = generate_question(
        subject="ekonomie",
        level="zakladni",
        topic="trh",
        strictness=3,
        sources=chunks,
        preview_len=250,
    )
    assert "[Zdroj: economics.pdf, str. 2]" in question.text
