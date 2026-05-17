from app.rag.chunk_strategies import chunk_by_strategy, chunk_classical_prose, chunk_poetry


def test_poetry_chunking_creates_whole_and_couplets() -> None:
    text = "床前明月光\n疑是地上霜\n举头望明月\n低头思故乡"
    chunks = chunk_poetry(text)

    assert chunks[0].chunk_type == "whole_poem"
    assert chunks[0].section_title == "整首"
    assert any(chunk.chunk_type == "poem_couplet" for chunk in chunks[1:])
    assert len(chunks) == 3


def test_classical_prose_chunking_uses_sentence_groups() -> None:
    text = "晋太元中，武陵人捕鱼为业。缘溪行，忘路之远近。忽逢桃花林，夹岸数百步，中无杂树，芳草鲜美，落英缤纷。"
    chunks = chunk_classical_prose(text)

    assert chunks
    assert all(chunk.chunk_type == "classical_sentence_group" for chunk in chunks)
    assert min(len(chunk.content) for chunk in chunks) > 20


def test_unknown_uses_modern_chunker() -> None:
    strategy, chunks = chunk_by_strategy("plain short text for fallback", "unknown")

    assert strategy == "modern"
    assert chunks[0].chunk_type == "paragraph_window"
