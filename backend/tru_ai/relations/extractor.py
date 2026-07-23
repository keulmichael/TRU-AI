from __future__ import annotations

import hashlib
import re

from tru_ai.parsing.models import ParsedSentence
from tru_ai.relations.models import (
    Proposition,
    Relation,
)
from tru_ai.relations.normalizer import (
    RelationNormalizer,
)
from tru_ai.relations.patterns import (
    RELATION_PATTERNS,
    RelationPattern,
)


class RelationExtractor:
    """Extrait des propositions et relations déterministes."""

    def __init__(
        self,
        normalizer: RelationNormalizer | None = None,
        patterns: tuple[
            RelationPattern,
            ...,
        ] = RELATION_PATTERNS,
    ) -> None:
        self.normalizer = (
            normalizer or RelationNormalizer()
        )
        self.patterns = patterns

    def extract_propositions(
        self,
        sentence: ParsedSentence,
    ) -> list[Proposition]:
        sentence_text = sentence.content.strip()

        if not sentence_text:
            return []

        clauses = self.split_clauses(sentence_text)
        propositions: list[Proposition] = []

        for clause_text, clause_start in clauses:
            proposition = self.extract_clause(
                sentence=sentence,
                clause_text=clause_text,
                clause_start=clause_start,
            )

            if proposition is not None:
                propositions.append(proposition)

        return propositions

    def extract_relations(
        self,
        sentence: ParsedSentence,
    ) -> list[Relation]:
        propositions = self.extract_propositions(
            sentence
        )

        return [
            self.proposition_to_relation(
                proposition
            )
            for proposition in propositions
        ]

    def extract(
        self,
        sentence: ParsedSentence,
    ) -> tuple[
        list[Proposition],
        list[Relation],
    ]:
        propositions = self.extract_propositions(
            sentence
        )

        relations = [
            self.proposition_to_relation(
                proposition
            )
            for proposition in propositions
        ]

        return propositions, relations

    def extract_clause(
        self,
        sentence: ParsedSentence,
        clause_text: str,
        clause_start: int,
    ) -> Proposition | None:
        for pattern in self.patterns:
            match = pattern.expression.match(
                clause_text
            )

            if match is None:
                continue

            subject_text = self.clean_component(
                match.group("subject")
            )

            predicate_text = self.clean_component(
                match.group("predicate")
            )

            object_text = self.clean_component(
                match.group("object")
            )

            if not self.is_valid_component(
                subject_text
            ):
                continue

            if not self.is_valid_component(
                object_text
            ):
                continue

            subject_normalized = (
                self.normalizer.normalize_entity(
                    subject_text
                )
            )

            predicate_normalized = (
                pattern.predicate_override
                or self.normalizer.normalize_predicate(
                    predicate_text
                )
            )

            object_normalized = (
                self.normalizer.normalize_entity(
                    object_text
                )
            )

            if (
                not subject_normalized
                or not predicate_normalized
                or not object_normalized
            ):
                continue

            clause_end = (
                clause_start + len(clause_text)
            )

            proposition_id = (
                self.build_identifier(
                    prefix="proposition",
                    parts=(
                        sentence.sentence_id,
                        subject_normalized,
                        predicate_normalized,
                        object_normalized,
                        str(clause_start),
                        str(clause_end),
                    ),
                )
            )

            return Proposition(
                proposition_id=proposition_id,
                sentence_id=sentence.sentence_id,
                document_id=sentence.document_id,
                section_id=sentence.section_id,
                paragraph_id=sentence.paragraph_id,
                subject_text=subject_text,
                predicate_text=predicate_text,
                object_text=object_text,
                subject_normalized=(
                    subject_normalized
                ),
                predicate_normalized=(
                    predicate_normalized
                ),
                object_normalized=(
                    object_normalized
                ),
                start_char=clause_start,
                end_char=clause_end,
                confidence=pattern.confidence,
                extraction_method=(
                    "deterministic_pattern"
                ),
                pattern_id=pattern.pattern_id,
            )

        return None

    def proposition_to_relation(
        self,
        proposition: Proposition,
    ) -> Relation:
        subject_id = self.build_identifier(
            prefix="entity",
            parts=(
                proposition.subject_normalized,
            ),
        )

        object_id = self.build_identifier(
            prefix="entity",
            parts=(
                proposition.object_normalized,
            ),
        )

        relation_id = self.build_identifier(
            prefix="relation",
            parts=(
                proposition.proposition_id,
                subject_id,
                proposition.predicate_normalized,
                object_id,
            ),
        )

        return Relation(
            relation_id=relation_id,
            proposition_id=(
                proposition.proposition_id
            ),
            sentence_id=proposition.sentence_id,
            subject_id=subject_id,
            subject_label=(
                proposition.subject_normalized
            ),
            predicate=(
                proposition.predicate_normalized
            ),
            object_id=object_id,
            object_label=(
                proposition.object_normalized
            ),
            confidence=proposition.confidence,
            extraction_method=(
                proposition.extraction_method
            ),
            pattern_id=proposition.pattern_id,
        )

    @staticmethod
    def split_clauses(
        sentence_text: str,
    ) -> list[tuple[str, int]]:
        clauses: list[tuple[str, int]] = []

        split_pattern = re.compile(
            r"\s*;\s*|"
            r"\s+mais\s+|"
            r"\s+tandis\s+que\s+|"
            r"\s+alors\s+que\s+",
            flags=re.IGNORECASE,
        )

        cursor = 0

        for match in split_pattern.finditer(
            sentence_text
        ):
            raw_clause = sentence_text[
                cursor:match.start()
            ]

            clause = raw_clause.strip()

            if clause:
                relative_start = raw_clause.find(
                    clause
                )

                clauses.append(
                    (
                        clause,
                        cursor + relative_start,
                    )
                )

            cursor = match.end()

        raw_clause = sentence_text[cursor:]
        clause = raw_clause.strip()

        if clause:
            relative_start = raw_clause.find(clause)

            clauses.append(
                (
                    clause,
                    cursor + relative_start,
                )
            )

        return clauses

    @staticmethod
    def clean_component(
        value: str,
    ) -> str:
        return value.strip(
            " \t\r\n,;:.!?\"“”«»()[]{}"
        )

    @staticmethod
    def is_valid_component(
        value: str,
    ) -> bool:
        if len(value) < 2:
            return False

        if len(value.split()) > 30:
            return False

        return any(
            character.isalpha()
            for character in value
        )

    @staticmethod
    def build_identifier(
        prefix: str,
        parts: tuple[str, ...],
    ) -> str:
        raw_identifier = "|".join(parts)

        digest = hashlib.sha256(
            raw_identifier.encode("utf-8")
        ).hexdigest()[:16]

        return f"{prefix}-{digest}"