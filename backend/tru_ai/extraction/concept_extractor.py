from __future__ import annotations

import hashlib
import re

from tru_ai.extraction.concept_lexicon import (
    ConceptLexicon,
)
from tru_ai.extraction.concept_models import (
    ConceptOccurrence,
)
from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)
from tru_ai.parsing.models import ParsedSentence


class ConceptExtractor:
    """Extrait les concepts à partir d'un lexique contrôlé."""

    def __init__(
        self,
        lexicon: ConceptLexicon | None = None,
        normalizer: LexicalNormalizer | None = None,
    ) -> None:
        self.normalizer = (
            normalizer or LexicalNormalizer()
        )

        self.lexicon = (
            lexicon
            or ConceptLexicon(
                normalizer=self.normalizer
            )
        )

    def extract(
        self,
        sentence: ParsedSentence,
    ) -> list[ConceptOccurrence]:
        normalized = (
            self.normalizer.normalize_with_mapping(
                sentence.content
            )
        )

        occupied_spans: list[tuple[int, int]] = []
        occurrences: list[ConceptOccurrence] = []

        for (
            normalized_alias,
            concept,
        ) in self.lexicon.aliases_by_length():
            pattern = self.build_alias_pattern(
                normalized_alias
            )

            for match in pattern.finditer(
                normalized.text
            ):
                normalized_start = match.start()
                normalized_end = match.end()

                if self.overlaps(
                    normalized_start,
                    normalized_end,
                    occupied_spans,
                ):
                    continue

                original_start = (
                    normalized.original_indexes[
                        normalized_start
                    ]
                )

                original_end = (
                    normalized.original_indexes[
                        normalized_end - 1
                    ]
                    + 1
                )

                matched_text = sentence.content[
                    original_start:original_end
                ]

                occurrence_id = (
                    self.build_occurrence_id(
                        sentence_id=sentence.sentence_id,
                        concept_id=concept.concept_id,
                        start_char=original_start,
                        end_char=original_end,
                    )
                )

                occurrences.append(
                    ConceptOccurrence(
                        occurrence_id=occurrence_id,
                        sentence_id=sentence.sentence_id,
                        concept_id=concept.concept_id,
                        preferred_label=(
                            concept.preferred_label
                        ),
                        category=concept.category,
                        matched_text=matched_text,
                        matched_alias=normalized_alias,
                        start_char=original_start,
                        end_char=original_end,
                        confidence=1.0,
                    )
                )

                occupied_spans.append(
                    (
                        normalized_start,
                        normalized_end,
                    )
                )

        return sorted(
            occurrences,
            key=lambda occurrence: (
                occurrence.start_char,
                occurrence.end_char,
                occurrence.concept_id,
            ),
        )

    @staticmethod
    def build_alias_pattern(
        normalized_alias: str,
    ) -> re.Pattern[str]:
        escaped_alias = re.escape(
            normalized_alias
        )

        return re.compile(
            rf"(?<![a-z0-9])"
            rf"{escaped_alias}"
            rf"(?![a-z0-9])"
        )

    @staticmethod
    def overlaps(
        start: int,
        end: int,
        occupied_spans: list[tuple[int, int]],
    ) -> bool:
        return any(
            start < occupied_end
            and end > occupied_start
            for occupied_start, occupied_end
            in occupied_spans
        )

    @staticmethod
    def build_occurrence_id(
        sentence_id: str,
        concept_id: str,
        start_char: int,
        end_char: int,
    ) -> str:
        raw_identifier = (
            f"{sentence_id}|{concept_id}|"
            f"{start_char}|{end_char}"
        )

        digest = hashlib.sha256(
            raw_identifier.encode("utf-8")
        ).hexdigest()[:16]

        return f"occurrence-{digest}"