from __future__ import annotations

import re

from tru_ai.parsing.models import ParsedParagraph, ParsedSentence


SENTENCE_BOUNDARY_PATTERN = re.compile(
    r"""
    (?<=[.!?…])
    ["»”')\]]*
    \s+
    (?=
        ["«“'(\[]*
        [A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ0-9]
    )
    """,
    flags=re.VERBOSE,
)


class SentenceSplitter:
    """Segmente des paragraphes français en phrases."""

    ABBREVIATIONS = {
        "m.",
        "mme.",
        "mlle.",
        "dr.",
        "pr.",
        "prof.",
        "etc.",
        "ex.",
        "cf.",
        "env.",
        "fig.",
        "vol.",
        "chap.",
        "art.",
        "n°.",
    }

    def split(
        self,
        paragraph: ParsedParagraph,
    ) -> list[ParsedSentence]:
        protected_content = self.protect_abbreviations(
            paragraph.content
        )

        raw_sentences = SENTENCE_BOUNDARY_PATTERN.split(
            protected_content
        )

        sentences: list[ParsedSentence] = []

        for raw_sentence in raw_sentences:
            content = self.restore_abbreviations(
                raw_sentence
            ).strip()

            if not content:
                continue

            position = len(sentences)

            sentences.append(
                ParsedSentence(
                    sentence_id=(
                        f"{paragraph.paragraph_id}-sentence-"
                        f"{position:05d}"
                    ),
                    document_id=paragraph.document_id,
                    section_id=paragraph.section_id,
                    paragraph_id=paragraph.paragraph_id,
                    position=position,
                    content=content,
                    word_count=len(content.split()),
                )
            )

        return sentences

    def protect_abbreviations(self, content: str) -> str:
        protected = content

        for abbreviation in self.ABBREVIATIONS:
            protected = re.sub(
                re.escape(abbreviation),
                lambda match: match.group(0).replace(
                    ".",
                    "<DOT>",
                ),
                protected,
                flags=re.IGNORECASE,
            )

        protected = re.sub(
            r"\b([A-ZÀ-Ý])\.",
            r"\1<DOT>",
            protected,
        )

        return protected

    @staticmethod
    def restore_abbreviations(content: str) -> str:
        return content.replace("<DOT>", ".")