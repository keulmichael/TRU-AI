from __future__ import annotations

import re

from tru_ai.parsing.models import ParsedParagraph, ParsedSection


HEADING_PATTERN = re.compile(
    r"^(#{1,6})\s+(.+?)\s*$",
    flags=re.MULTILINE,
)


class MarkdownParser:
    """Transforme un document Markdown en sections et paragraphes."""

    def parse_sections(
        self,
        document_id: str,
        content: str,
    ) -> list[ParsedSection]:
        matches = list(HEADING_PATTERN.finditer(content))

        if not matches:
            normalized_content = self.normalize_block(content)

            return [
                ParsedSection(
                    section_id=f"{document_id}-section-00000",
                    document_id=document_id,
                    position=0,
                    level=1,
                    title="Document",
                    content=normalized_content,
                )
            ]

        sections: list[ParsedSection] = []

        introduction = self.normalize_block(
            content[: matches[0].start()]
        )

        if introduction:
            sections.append(
                ParsedSection(
                    section_id=f"{document_id}-section-00000",
                    document_id=document_id,
                    position=0,
                    level=0,
                    title="Préambule",
                    content=introduction,
                )
            )

        for match_position, match in enumerate(matches):
            content_start = match.end()

            if match_position + 1 < len(matches):
                content_end = matches[match_position + 1].start()
            else:
                content_end = len(content)

            section_content = self.normalize_block(
                content[content_start:content_end]
            )

            section_position = len(sections)

            sections.append(
                ParsedSection(
                    section_id=(
                        f"{document_id}-section-"
                        f"{section_position:05d}"
                    ),
                    document_id=document_id,
                    position=section_position,
                    level=len(match.group(1)),
                    title=match.group(2).strip(),
                    content=section_content,
                )
            )

        return sections

    def parse_paragraphs(
        self,
        section: ParsedSection,
    ) -> list[ParsedParagraph]:
        if not section.content:
            return []

        raw_paragraphs = re.split(
            r"\n\s*\n",
            section.content,
        )

        paragraphs: list[ParsedParagraph] = []

        for raw_paragraph in raw_paragraphs:
            content = self.normalize_block(raw_paragraph)

            if not content:
                continue

            position = len(paragraphs)

            paragraphs.append(
                ParsedParagraph(
                    paragraph_id=(
                        f"{section.section_id}-paragraph-"
                        f"{position:05d}"
                    ),
                    document_id=section.document_id,
                    section_id=section.section_id,
                    position=position,
                    content=content,
                )
            )

        return paragraphs

    @staticmethod
    def normalize_block(content: str) -> str:
        content = content.replace("\r\n", "\n")
        content = content.replace("\r", "\n")
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r" *\n *", "\n", content)
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()