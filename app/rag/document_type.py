import re
from dataclasses import dataclass
from typing import Dict, Optional


DOCUMENT_TYPES = {
    "english_fiction",
    "modern_chinese",
    "classical_poetry",
    "classical_prose",
    "poetry_or_lyrics",
    "unknown",
}


@dataclass
class DocumentTypeResult:
    document_type: str
    confidence: float
    reason: str
    chunk_strategy: str


class DocumentTypeDetector:
    classical_particles = set("之乎者也矣焉哉其乃若夫盖惟兮曰为于以而")
    modern_markers = {"的", "了", "是", "在", "我们", "他们", "但是", "因为", "所以"}

    def detect(self, text: str) -> DocumentTypeResult:
        sample = text.strip()
        if not sample:
            return DocumentTypeResult("unknown", 0.0, "文本为空。", "modern")

        stats = self._stats(sample)

        if stats["english_ratio"] >= 0.55:
            return DocumentTypeResult(
                "english_fiction",
                min(0.95, stats["english_ratio"]),
                "英文字符占比较高，按英文文学长文本处理。",
                "modern",
            )

        poetry = self._detect_classical_poetry(sample, stats)
        if poetry:
            return poetry

        classical = self._detect_classical_prose(stats)
        if classical:
            return classical

        if stats["line_count"] >= 6 and stats["avg_line_len"] <= 24:
            return DocumentTypeResult(
                "poetry_or_lyrics",
                0.68,
                "文本呈现多行短句结构，但不完全符合古诗词定长句式。",
                "poetry",
            )

        if stats["cjk_ratio"] >= 0.35:
            return DocumentTypeResult(
                "modern_chinese",
                0.72,
                "中文字符和现代标点占比较高，按现代中文文学文本处理。",
                "modern",
            )

        return DocumentTypeResult(
            "unknown",
            0.45,
            "无法稳定判断体裁，回退到通用长文本切分策略。",
            "modern",
        )

    def _stats(self, text: str) -> Dict[str, float]:
        chars = [char for char in text if not char.isspace()]
        total = max(len(chars), 1)
        cjk_count = sum(1 for char in chars if "\u4e00" <= char <= "\u9fff")
        english_count = sum(1 for char in chars if char.isascii() and char.isalpha())
        punctuation_count = sum(1 for char in chars if char in "，。！？；：,.!?;:")
        classical_count = sum(1 for char in chars if char in self.classical_particles)
        modern_count = sum(text.count(token) for token in self.modern_markers)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        line_lengths = [self._cjk_len(line) for line in lines]
        avg_line_len = sum(line_lengths) / max(len(line_lengths), 1)
        regular_poem_lines = sum(1 for length in line_lengths if 4 <= length <= 9)
        five_or_seven_lines = sum(1 for length in line_lengths if length in {5, 7})

        return {
            "cjk_ratio": cjk_count / total,
            "english_ratio": english_count / total,
            "punctuation_ratio": punctuation_count / total,
            "classical_ratio": classical_count / max(cjk_count, 1),
            "modern_density": modern_count / max(cjk_count, 1),
            "line_count": float(len(lines)),
            "avg_line_len": avg_line_len,
            "regular_poem_ratio": regular_poem_lines / max(len(lines), 1),
            "five_or_seven_ratio": five_or_seven_lines / max(len(lines), 1),
            "char_count": float(len(text)),
        }

    def _detect_classical_poetry(
        self, text: str, stats: Dict[str, float]
    ) -> Optional[DocumentTypeResult]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sentence_units = [
            unit for unit in re.split(r"[，,。！？；;!?]\s*", text) if unit.strip()
        ]
        has_line_structure = len(lines) >= 2
        units = lines if has_line_structure else sentence_units
        unit_lengths = [self._cjk_len(unit) for unit in units]
        if not unit_lengths:
            return None

        short_regular_ratio = sum(1 for length in unit_lengths if 4 <= length <= 12) / len(unit_lengths)
        five_or_seven_ratio = sum(1 for length in unit_lengths if length in {5, 7}) / len(unit_lengths)
        compact_short_poem = (
            has_line_structure
            and 2 <= len(unit_lengths) <= 16
            and stats["char_count"] <= 800
            and short_regular_ratio >= 0.65
        )
        regulated_poem = 4 <= len(unit_lengths) <= 8 and five_or_seven_ratio >= 0.75

        if regulated_poem:
            return DocumentTypeResult(
                "classical_poetry",
                0.9,
                "文本由多行五言或七言句式构成，符合绝句/律诗特征。",
                "poetry",
            )
        if compact_short_poem and stats["classical_ratio"] >= 0.015:
            return DocumentTypeResult(
                "classical_poetry",
                0.76,
                "文本篇幅短、句式整齐，并含文言/古典表达特征。",
                "poetry",
            )
        return None

    def _detect_classical_prose(
        self, stats: Dict[str, float]
    ) -> Optional[DocumentTypeResult]:
        if (
            stats["cjk_ratio"] >= 0.45
            and stats["classical_ratio"] >= 0.035
            and stats["modern_density"] < 0.045
        ):
            return DocumentTypeResult(
                "classical_prose",
                0.78,
                "文言虚词比例较高，现代白话标记较少，按文言文句群处理。",
                "classical_prose",
            )
        return None

    def _cjk_len(self, text: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fff]", text))


document_type_detector = DocumentTypeDetector()
