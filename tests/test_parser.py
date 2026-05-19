from io import BytesIO
from zipfile import ZipFile

import pytest

from app.rag.parser import UnsupportedDocumentError, parse_document


def _sample_epub() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )
        archive.writestr(
            "OPS/content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="chap1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chap2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chap1"/>
    <itemref idref="chap2"/>
  </spine>
</package>
""",
        )
        archive.writestr("OPS/chapter1.xhtml", "<html><body><h1>第一章</h1><p>月光落在窗前。</p></body></html>")
        archive.writestr("OPS/chapter2.xhtml", "<html><body><p>远行的人想起故乡。</p></body></html>")
    return buffer.getvalue()


def _sample_pdf() -> bytes:
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 24 Tf 100 700 Td (Hello PDF Text) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000241 00000 n 
0000000311 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
405
%%EOF
"""


def test_parse_epub_extracts_spine_text() -> None:
    text = parse_document("sample.epub", _sample_epub())

    assert "第一章" in text
    assert "月光落在窗前" in text
    assert text.index("第一章") < text.index("远行的人")


def test_parse_pdf_extracts_text() -> None:
    text = parse_document("sample.pdf", _sample_pdf())

    assert "第 1 页" in text
    assert "Hello PDF Text" in text


def test_parse_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedDocumentError):
        parse_document("sample.docx", b"hello")
