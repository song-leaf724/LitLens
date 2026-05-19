import os
import re
import zipfile
from html.parser import HTMLParser
from io import BytesIO
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".epub"}
TEXT_EXTENSIONS = {".txt", ".md"}
EPUB_TEXT_MEDIA_TYPES = {
    "application/xhtml+xml",
    "text/html",
}


class UnsupportedDocumentError(ValueError):
    pass


class _HTMLTextExtractor(HTMLParser):
    block_tags = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "p",
        "section",
        "tr",
    }
    ignored_tags = {"script", "style", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        if tag in self.ignored_tags:
            self._ignored_depth += 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        cleaned = data.replace("\xa0", " ").strip()
        if cleaned:
            self.parts.append(cleaned)

    def text(self) -> str:
        return _normalize_text(" ".join(self.parts))


def parse_document(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentError(
            f"暂不支持 {ext or '未知'} 文件类型，请上传 {supported} 文件。"
        )

    if ext in TEXT_EXTENSIONS:
        text = _parse_plain_text(content)
    elif ext == ".pdf":
        text = _parse_pdf(content)
    elif ext == ".epub":
        text = _parse_epub(content)
    else:  # pragma: no cover - guarded by SUPPORTED_EXTENSIONS
        raise UnsupportedDocumentError(f"暂不支持 {ext} 文件类型。")

    normalized = _normalize_text(text)
    if not normalized:
        raise ValueError("文档内容为空，无法进行文学分析。")
    return normalized


def _parse_plain_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("文档解析失败，请确认文件编码为 UTF-8 或常见中文编码。")


def _parse_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on environment setup
        raise UnsupportedDocumentError("当前环境未安装 pypdf，请先运行 pip install -r requirements.txt。") from exc

    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:  # pragma: no cover - depends on specific PDF
                raise ValueError("PDF 文件已加密，无法解析文本。") from exc
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"第 {index} 页\n{page_text.strip()}")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("PDF 解析失败，请确认文件不是扫描版图片或损坏文件。") from exc

    text = "\n\n".join(pages)
    if not text.strip():
        raise ValueError("PDF 中没有提取到可分析文本；如果是扫描版 PDF，需要先做 OCR。")
    return text


def _parse_epub(content: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            html_paths = _epub_reading_order(archive)
            if not html_paths:
                html_paths = sorted(
                    name
                    for name in archive.namelist()
                    if name.lower().endswith((".xhtml", ".html", ".htm"))
                )
            sections = []
            for path in html_paths:
                try:
                    raw = archive.read(path)
                except KeyError:
                    continue
                section = _extract_html_text(raw)
                if section:
                    sections.append(section)
    except zipfile.BadZipFile as exc:
        raise ValueError("EPUB 解析失败，请确认文件格式正确。") from exc

    text = "\n\n".join(sections)
    if not text.strip():
        raise ValueError("EPUB 中没有提取到可分析文本。")
    return text


def _epub_reading_order(archive: zipfile.ZipFile) -> List[str]:
    opf_path = _find_opf_path(archive)
    if not opf_path:
        return []

    try:
        opf_root = ET.fromstring(archive.read(opf_path))
    except ET.ParseError:
        return []

    namespace = _xml_namespace(opf_root.tag)
    ns = {"opf": namespace} if namespace else {}
    manifest_items = opf_root.findall(".//opf:manifest/opf:item", ns) if ns else opf_root.findall(".//manifest/item")
    spine_items = opf_root.findall(".//opf:spine/opf:itemref", ns) if ns else opf_root.findall(".//spine/itemref")

    manifest: Dict[str, str] = {}
    for item in manifest_items:
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        media_type = item.attrib.get("media-type")
        if not item_id or not href or media_type not in EPUB_TEXT_MEDIA_TYPES:
            continue
        manifest[item_id] = _join_epub_path(opf_path, href)

    ordered = []
    for itemref in spine_items:
        href = manifest.get(itemref.attrib.get("idref", ""))
        if href:
            ordered.append(href)
    return ordered


def _find_opf_path(archive: zipfile.ZipFile) -> Optional[str]:
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
    except (KeyError, ET.ParseError):
        candidates = [name for name in archive.namelist() if name.lower().endswith(".opf")]
        return sorted(candidates)[0] if candidates else None

    for element in container.iter():
        if element.tag.endswith("rootfile"):
            full_path = element.attrib.get("full-path")
            if full_path:
                return full_path
    return None


def _xml_namespace(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[1 : tag.index("}")]
    return ""


def _join_epub_path(opf_path: str, href: str) -> str:
    base = os.path.dirname(opf_path)
    return os.path.normpath(os.path.join(base, href)).replace("\\", "/")


def _extract_html_text(raw: bytes) -> str:
    html = _decode_html(raw)
    extractor = _HTMLTextExtractor()
    extractor.feed(html)
    return extractor.text()


def _decode_html(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    lines = [line.strip() for line in normalized.split("\n")]
    compact_lines = []
    blank_seen = False
    for line in lines:
        if not line:
            if not blank_seen and compact_lines:
                compact_lines.append("")
            blank_seen = True
            continue
        compact_lines.append(line)
        blank_seen = False
    return "\n".join(compact_lines).strip()
