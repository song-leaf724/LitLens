import os


SUPPORTED_EXTENSIONS = {".txt", ".md"}


class UnsupportedDocumentError(ValueError):
    pass


def parse_document(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDocumentError(
            f"暂不支持 {ext or '未知'} 文件类型，请上传 .txt 或 .md 文件。"
        )

    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            text = ""
    if not text:
        raise ValueError("文档解析失败，请确认文件编码为 UTF-8 或常见中文编码。")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise ValueError("文档内容为空，无法进行文学分析。")
    return normalized

