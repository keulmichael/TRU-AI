from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".md": "markdown",
    ".txt": "text",
}


@dataclass(frozen=True)
class ExtractedBlock:
    block_type: str
    text: str
    page_number: int | None
    order: int
    level: int | None = None


@dataclass(frozen=True)
class ExtractedDocument:
    path: Path
    format: str
    title: str
    blocks: tuple[ExtractedBlock, ...]
    page_count: int
    extracted_page_count: int
    empty_page_numbers: tuple[int, ...]
    extraction_errors: tuple[str, ...]


class DocumentImporter:
    def __init__(self, sources_directory: Path) -> None:
        self.sources_directory = sources_directory

    def discover(self) -> tuple[Path, ...]:
        if not self.sources_directory.exists():
            return ()
        return tuple(
            sorted(
                path
                for path in self.sources_directory.rglob("*")
                if path.is_file()
                and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )
        )

    def import_path(self, path: Path) -> ExtractedDocument:
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Format non supporté : {path}")
        if extension == ".pdf":
            return self._import_pdf(path)
        if extension == ".docx":
            return self._import_docx(path)
        return self._import_text(path, SUPPORTED_EXTENSIONS[extension])

    def _import_text(self, path: Path, fmt: str) -> ExtractedDocument:
        content = path.read_text(encoding="utf-8-sig")
        blocks: list[ExtractedBlock] = []
        order = 0
        for paragraph in re.split(r"\n\s*\n", content):
            text = paragraph.strip()
            if not text:
                continue
            level = None
            block_type = "paragraph"
            heading = re.match(r"^(#{1,6})\s+(.+)$", text)
            if heading:
                block_type = "heading"
                level = len(heading.group(1))
                text = heading.group(2).strip()
            blocks.append(
                ExtractedBlock(
                    block_type=block_type,
                    text=text,
                    page_number=1,
                    order=order,
                    level=level,
                )
            )
            order += 1
        title = self._title_from_blocks(path, blocks)
        return ExtractedDocument(
            path=path,
            format=fmt,
            title=title,
            blocks=tuple(blocks),
            page_count=1,
            extracted_page_count=1 if blocks else 0,
            empty_page_numbers=() if blocks else (1,),
            extraction_errors=(),
        )

    def _import_pdf(self, path: Path) -> ExtractedDocument:
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError(
                "Le support PDF nécessite le paquet pypdf."
            ) from error
        reader = PdfReader(str(path))
        blocks: list[ExtractedBlock] = []
        empty_pages: list[int] = []
        errors: list[str] = []
        order = 0
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = (page.extract_text() or "").strip()
            except Exception as error:  # pragma: no cover - defensive
                errors.append(f"page {index}: {error}")
                continue
            if not text:
                empty_pages.append(index)
                continue
            for block_type, cleaned, level in self._split_pdf_page(text):
                blocks.append(
                    ExtractedBlock(
                        block_type=block_type,
                        text=cleaned,
                        page_number=index,
                        order=order,
                        level=level,
                    )
                )
                order += 1
        return ExtractedDocument(
            path=path,
            format="pdf",
            title=path.stem.replace("-", " ").replace("_", " "),
            blocks=tuple(blocks),
            page_count=len(reader.pages),
            extracted_page_count=len(
                {
                    block.page_number
                    for block in blocks
                    if block.page_number is not None
                }
            ),
            empty_page_numbers=tuple(empty_pages),
            extraction_errors=tuple(errors),
        )

    @staticmethod
    def _split_pdf_page(text: str) -> list[tuple[str, str, int | None]]:
        blocks: list[tuple[str, str, int | None]] = []
        paragraph_lines: list[str] = []

        def flush() -> None:
            if not paragraph_lines:
                return
            value = " ".join(" ".join(paragraph_lines).split())
            paragraph_lines.clear()
            if value:
                blocks.append(("paragraph", value, None))

        for raw_line in text.splitlines():
            line = " ".join(raw_line.strip().split())
            if not line:
                flush()
                continue

            lowered = line.lower()
            is_heading = (
                len(line) <= 96
                and not line.endswith((".", ";", ",", ":"))
                and (
                    lowered.startswith(("volume", "partie", "chapitre"))
                    or line.isupper()
                )
            )

            if is_heading:
                flush()
                level = 1
                if lowered.startswith("volume"):
                    level = 0
                elif lowered.startswith("partie"):
                    level = 0
                blocks.append(("heading", line, level))
                continue

            paragraph_lines.append(line)
            if line.endswith((".", "!", "?")):
                flush()

        flush()
        return blocks

    def _import_docx(self, path: Path) -> ExtractedDocument:
        namespace = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }
        blocks: list[ExtractedBlock] = []
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(document_xml)
        order = 0
        for child in root.findall(".//w:body/*", namespace):
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "p":
                text = self._docx_text(child, namespace)
                if not text:
                    continue
                style = child.find(".//w:pStyle", namespace)
                value = (
                    style.attrib.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val",
                        "",
                    )
                    if style is not None
                    else ""
                )
                heading = re.match(r"Heading([1-6])", value)
                blocks.append(
                    ExtractedBlock(
                        block_type="heading" if heading else "paragraph",
                        text=text,
                        page_number=None,
                        order=order,
                        level=int(heading.group(1)) if heading else None,
                    )
                )
                order += 1
            elif tag == "tbl":
                rows = []
                for row in child.findall(".//w:tr", namespace):
                    cells = [
                        self._docx_text(cell, namespace)
                        for cell in row.findall(".//w:tc", namespace)
                    ]
                    rows.append(" | ".join(cell for cell in cells if cell))
                text = "\n".join(row for row in rows if row).strip()
                if text:
                    blocks.append(
                        ExtractedBlock(
                            block_type="table",
                            text=text,
                            page_number=None,
                            order=order,
                        )
                    )
                    order += 1
        return ExtractedDocument(
            path=path,
            format="docx",
            title=self._title_from_blocks(path, blocks),
            blocks=tuple(blocks),
            page_count=0,
            extracted_page_count=0,
            empty_page_numbers=(),
            extraction_errors=(),
        )

    @staticmethod
    def _docx_text(element, namespace: dict[str, str]) -> str:
        return " ".join(
            text.text or ""
            for text in element.findall(".//w:t", namespace)
        ).strip()

    @staticmethod
    def _title_from_blocks(path: Path, blocks: list[ExtractedBlock]) -> str:
        for block in blocks:
            if block.block_type == "heading":
                return block.text
        return path.stem.replace("-", " ").replace("_", " ").strip()
