import re
from typing import List, Tuple

from app.core.config import settings
from app.rag.chunker import TextChunk, chunk_text


def chunk_by_strategy(text: str, document_type: str) -> Tuple[str, List[TextChunk]]:
    strategy = select_chunk_strategy(document_type)
    if strategy == "poetry":
        return strategy, chunk_poetry(text)
    if strategy == "classical_prose":
        return strategy, chunk_classical_prose(text)
    return strategy, chunk_modern_text(text)


def select_chunk_strategy(document_type: str) -> str:
    if document_type in {"classical_poetry", "poetry_or_lyrics"}:
        return "poetry"
    if document_type == "classical_prose":
        return "classical_prose"
    return "modern"


def chunk_modern_text(text: str) -> List[TextChunk]:
    chunks = chunk_text(
        text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    for chunk in chunks:
        chunk.chunk_type = "paragraph_window"
        chunk.metadata = {"strategy": "modern"}
    return chunks


def chunk_poetry(text: str) -> List[TextChunk]:
    cleaned = _normalize(text)
    if not cleaned:
        return []

    chunks: List[TextChunk] = [
        TextChunk(
            chunk_index=0,
            content=cleaned,
            start_char=0,
            end_char=len(cleaned),
            chunk_type="whole_poem",
            section_title="整首",
            metadata={"strategy": "poetry"},
        )
    ]

    units = _poetry_units(cleaned)
    cursor = 0
    for pair_index, pair in enumerate(_group_units(units, size=2), start=1):
        content = "\n".join(pair).strip()
        if not content or content == cleaned:
            continue
        start = cleaned.find(pair[0], cursor)
        if start < 0:
            start = cleaned.find(pair[0])
        end = start + len(content) if start >= 0 else len(cleaned)
        cursor = max(end, cursor)
        chunks.append(
            TextChunk(
                chunk_index=len(chunks),
                content=content,
                start_char=max(start, 0),
                end_char=min(end, len(cleaned)),
                chunk_type="poem_couplet",
                section_title=f"句组 {pair_index}",
                metadata={"strategy": "poetry", "unit_count": str(len(pair))},
            )
        )
    return chunks


def chunk_classical_prose(text: str) -> List[TextChunk]:
    cleaned = _normalize(text)
    if not cleaned:
        return []

    groups: List[TextChunk] = []
    cursor = 0
    for paragraph_index, paragraph in enumerate(_paragraphs(cleaned), start=1):
        sentences = _classical_sentences(paragraph)
        buffer: List[str] = []
        for sentence in sentences:
            buffer.append(sentence)
            content = "".join(buffer).strip()
            if len(content) >= 180:
                groups.append(
                    _make_classical_chunk(cleaned, content, paragraph_index, len(groups), cursor)
                )
                cursor = groups[-1].end_char
                buffer = []
        if buffer:
            content = "".join(buffer).strip()
            if groups and len(content) < 60 and groups[-1].section_title == f"第 {paragraph_index} 段":
                groups[-1].content = f"{groups[-1].content}{content}"
                groups[-1].end_char = min(groups[-1].end_char + len(content), len(cleaned))
            else:
                groups.append(
                    _make_classical_chunk(cleaned, content, paragraph_index, len(groups), cursor)
                )
                cursor = groups[-1].end_char

    for index, chunk in enumerate(groups):
        chunk.chunk_index = index
    return groups


def _make_classical_chunk(
    full_text: str, content: str, paragraph_index: int, chunk_index: int, cursor: int
) -> TextChunk:
    start = full_text.find(content[: min(len(content), 20)], cursor)
    if start < 0:
        start = full_text.find(content[: min(len(content), 20)])
    if start < 0:
        start = cursor
    end = min(start + len(content), len(full_text))
    return TextChunk(
        chunk_index=chunk_index,
        content=content,
        start_char=start,
        end_char=end,
        chunk_type="classical_sentence_group",
        section_title=f"第 {paragraph_index} 段",
        metadata={"strategy": "classical_prose"},
    )


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _paragraphs(text: str) -> List[str]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if parts:
        return parts
    return [text]


def _poetry_units(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 2:
        return lines
    units = [unit.strip() for unit in re.split(r"(?<=[。！？；;!?])", text) if unit.strip()]
    return units or [text]


def _group_units(units: List[str], size: int) -> List[List[str]]:
    return [units[index : index + size] for index in range(0, len(units), size)]


def _classical_sentences(text: str) -> List[str]:
    sentences = re.findall(r".+?[。！？；;!?]|.+$", text, flags=re.S)
    return [sentence.strip() for sentence in sentences if sentence.strip()]
