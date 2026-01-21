from app.core.local_sources import SourceChunk
from app.core.question_engine import generate_lesson_from_sources


def test_generate_lesson_basic():
    # Create a fake source with an explicit question section
    text = (
        "Názorné otázky:\n"
        "1) Co je inflace?\n"
        "2) Jak se meri HDP?\n\n"
        "Toto je dalsi text o ekonomii a makroekonomickych pojmech, popis trhu a poptavky."
    )
    chunks = [SourceChunk(text=text, source="test"), SourceChunk(text="dalsi text o trhu a poptavce", source="test")]

    lesson = generate_lesson_from_sources(
        chunks,
        subject="ekonomie",
        level="zakladni",
        strictness=3,
        n_total=8,
        preview_len=120,
    )
    assert isinstance(lesson, list)
    assert len(lesson) >= 8
    # Should contain at least one explicit and one generated marker
    assert any(item.startswith("[From document]") for item in lesson)
    assert any(item.startswith("[Generated]") for item in lesson)
    # Should include a document preview for generated questions
    assert any("[From document:" in item for item in lesson)


def test_generate_lesson_no_sources():
    assert generate_lesson_from_sources([], subject="ekonomie", level="zakladni", strictness=3, n_total=3) == []
