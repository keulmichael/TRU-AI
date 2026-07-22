from __future__ import annotations

from dataclasses import dataclass

from tru_ai.extraction.corpus import CorpusDocument
from tru_ai.parsing.markdown_parser import MarkdownParser
from tru_ai.parsing.models import (
    ParsedParagraph,
    ParsedSection,
    ParsedSentence,
)
from tru_ai.parsing.sentence_splitter import SentenceSplitter


@dataclass(frozen=True)
class ParsingResult:
    sections: list[ParsedSection]
    paragraphs: list[ParsedParagraph]
    sentences: list[ParsedSentence]


class ParsingPipeline:
    """Coordonne l’analyse structurelle et linguistique."""

    def __init__(
        self,
        markdown_parser: MarkdownParser | None = None,
        sentence_splitter: SentenceSplitter | None = None,
    ) -> None:
        self.markdown_parser = (
            markdown_parser or MarkdownParser()
        )

        self.sentence_splitter = (
            sentence_splitter or SentenceSplitter()
        )

    def process(
        self,
        documents: list[CorpusDocument],
    ) -> ParsingResult:
        sections: list[ParsedSection] = []
        paragraphs: list[ParsedParagraph] = []
        sentences: list[ParsedSentence] = []

        for document in documents:
            document_sections = (
                self.markdown_parser.parse_sections(
                    document_id=document.document_id,
                    content=document.content,
                )
            )

            sections.extend(document_sections)

            for section in document_sections:
                section_paragraphs = (
                    self.markdown_parser.parse_paragraphs(
                        section
                    )
                )

                paragraphs.extend(section_paragraphs)

                for paragraph in section_paragraphs:
                    paragraph_sentences = (
                        self.sentence_splitter.split(
                            paragraph
                        )
                    )

                    sentences.extend(paragraph_sentences)

        return ParsingResult(
            sections=sections,
            paragraphs=paragraphs,
            sentences=sentences,
        )