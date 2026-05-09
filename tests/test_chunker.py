from app.rag.chunker import chunk_text


def test_chunk_text_returns_ordered_chunks() -> None:
    text = "第一章\n这是一个开始。" * 80
    chunks = chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].start_char < chunks[0].end_char
    assert chunks[1].start_char < chunks[1].end_char
    assert chunks[0].content


def test_chunk_text_handles_empty_text() -> None:
    assert chunk_text("") == []

