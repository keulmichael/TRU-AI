from __future__ import annotations

import zipfile

from pypdf import PdfWriter

from tru_ai.memory.importer import DocumentImporter


def make_docx(path):
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Chapitre Delta</w:t></w:r></w:p>
    <w:p><w:r><w:t>Delta est défini comme l'écart entre état prédit et état observé.</w:t></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Terme</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Delta</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
  </w:body>
</w:document>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)


def test_importer_discovers_supported_sources(tmp_path):
    (tmp_path / "a.md").write_text("# Delta\n\nDelta est défini.", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Texte", encoding="utf-8")
    (tmp_path / "ignored.csv").write_text("x", encoding="utf-8")

    paths = DocumentImporter(tmp_path).discover()

    assert [path.name for path in paths] == ["a.md", "b.txt"]


def test_importer_reads_markdown_headings(tmp_path):
    path = tmp_path / "delta.md"
    path.write_text(
        "# Delta\n\nDelta est défini comme l'écart réflexif.",
        encoding="utf-8",
    )

    document = DocumentImporter(tmp_path).import_path(path)

    assert document.format == "markdown"
    assert document.title == "Delta"
    assert [block.block_type for block in document.blocks] == [
        "heading",
        "paragraph",
    ]


def test_importer_reads_docx_structure_and_tables(tmp_path):
    path = tmp_path / "delta.docx"
    make_docx(path)

    document = DocumentImporter(tmp_path).import_path(path)

    assert document.format == "docx"
    assert document.title == "Chapitre Delta"
    assert [block.block_type for block in document.blocks] == [
        "heading",
        "paragraph",
        "table",
    ]
    assert "Delta" in document.blocks[-1].text


def test_importer_detects_empty_pdf_pages(tmp_path):
    path = tmp_path / "empty.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as output:
        writer.write(output)

    document = DocumentImporter(tmp_path).import_path(path)

    assert document.format == "pdf"
    assert document.page_count == 2
    assert document.extracted_page_count == 0
    assert document.empty_page_numbers == (1, 2)
