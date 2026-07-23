from __future__ import annotations

import hashlib

from tru_ai.extraction.concept_lexicon import (
    ConceptLexicon,
)
from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)
from tru_ai.graph.models import GraphNode


class EntityResolver:
    """
    Résout une étiquette d'entité vers un concept TRU
    ou vers une entité générique stable.
    """

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

        self._concept_by_alias = (
            self.build_concept_alias_index()
        )

    def resolve(
        self,
        label: str,
    ) -> GraphNode:
        normalized_label = (
            self.normalizer.normalize(label)
        )

        concept = self._concept_by_alias.get(
            normalized_label
        )

        if concept is not None:
            return GraphNode(
                node_id=(
                    f"concept-{concept.concept_id}"
                ),
                label=concept.preferred_label,
                normalized_label=(
                    self.normalizer.normalize(
                        concept.preferred_label
                    )
                ),
                node_type="concept",
                concept_id=concept.concept_id,
                category=concept.category,
                aliases={
                    label,
                    concept.preferred_label,
                },
            )

        return GraphNode(
            node_id=self.build_entity_id(
                normalized_label
            ),
            label=label,
            normalized_label=normalized_label,
            node_type="entity",
            aliases={label},
        )

    def build_concept_alias_index(
        self,
    ) -> dict:
        index = {}

        for concept in self.lexicon.all_concepts():
            labels = (
                concept.preferred_label,
                *concept.aliases,
            )

            for label in labels:
                normalized_label = (
                    self.normalizer.normalize(label)
                )

                index[normalized_label] = concept

        return index

    @staticmethod
    def build_entity_id(
        normalized_label: str,
    ) -> str:
        digest = hashlib.sha256(
            normalized_label.encode("utf-8")
        ).hexdigest()[:16]

        return f"entity-{digest}"