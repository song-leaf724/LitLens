from dataclasses import dataclass
from typing import List


@dataclass
class TextChunk:
    chunk_index: int
    content: str
    start_char: int
    end_char: int


def _find_breakpoint(text: str, start: int, hard_end: int, min_end: int) -> int:
    candidates = ["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
    window = text[min_end:hard_end]
    best = -1
    best_len = 0
    for token in candidates:
        pos = window.rfind(token)
        if pos > best:
            best = pos
            best_len = len(token)
    if best < 0:
        return hard_end
    return min_end + best + best_len


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[TextChunk]:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return []

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    chunks: List[TextChunk] = []
    start = 0
    length = len(cleaned)

    while start < length:
        hard_end = min(start + chunk_size, length)
        if hard_end < length:
            min_end = min(start + max(chunk_size // 2, 1), hard_end)
            end = _find_breakpoint(cleaned, start, hard_end, min_end)
        else:
            end = hard_end

        raw_content = cleaned[start:end]
        leading = len(raw_content) - len(raw_content.lstrip())
        trailing = len(raw_content) - len(raw_content.rstrip())
        content = raw_content.strip()

        if content:
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    content=content,
                    start_char=start + leading,
                    end_char=end - trailing,
                )
            )

        if end >= length:
            break
        next_start = max(0, end - overlap)
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks

