from tru_ai.parsing.models import ParsedParagraph
from tru_ai.parsing.sentence_splitter import SentenceSplitter


def make_paragraph(content: str) -> ParsedParagraph:
    return ParsedParagraph(
        paragraph_id="paragraph-001",
        document_id="document-001",
        section_id="section-001",
        position=0,
        content=content,
    )


def test_splitter_extracts_sentences() -> None:
    paragraph = make_paragraph(
        "La conscience observe. "
        "Elle compare ensuite les états. "
        "La reconnaissance devient-elle possible ?"
    )

    splitter = SentenceSplitter()
    sentences = splitter.split(paragraph)

    assert len(sentences) == 3
    assert sentences[0].content == "La conscience observe."
    assert sentences[1].content == (
        "Elle compare ensuite les états."
    )


def test_splitter_preserves_abbreviations() -> None:
    paragraph = make_paragraph(
        "Le Dr. Martin observe le phénomène. "
        "Il formule ensuite une hypothèse."
    )

    splitter = SentenceSplitter()
    sentences = splitter.split(paragraph)

    assert len(sentences) == 2
    assert "Dr. Martin" in sentences[0].content