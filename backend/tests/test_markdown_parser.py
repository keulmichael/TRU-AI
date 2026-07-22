from tru_ai.parsing.markdown_parser import MarkdownParser


def test_parser_extracts_markdown_sections() -> None:
    content = """
# Introduction

Premier paragraphe.

## Reconnaissance

Deuxième paragraphe.
""".strip()

    parser = MarkdownParser()

    sections = parser.parse_sections(
        document_id="document-001",
        content=content,
    )

    assert len(sections) == 2

    assert sections[0].title == "Introduction"
    assert sections[0].level == 1

    assert sections[1].title == "Reconnaissance"
    assert sections[1].level == 2


def test_parser_extracts_paragraphs() -> None:
    content = """
# Introduction

Premier paragraphe.

Deuxième paragraphe.
""".strip()

    parser = MarkdownParser()

    sections = parser.parse_sections(
        document_id="document-001",
        content=content,
    )

    paragraphs = parser.parse_paragraphs(
        sections[0]
    )

    assert len(paragraphs) == 2
    assert paragraphs[0].content == "Premier paragraphe."
    assert paragraphs[1].content == "Deuxième paragraphe."