from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_string_sequence,
    normalize_text,
)
from tru_ai.cognitive.reasoning.models import (
    RecognitionRelation,
    ReasoningStage,
    ReasoningStep,
)


class ContradictionEngine:
    """
    Extrait les contradictions déclarées et analyse les métadonnées explicites.

    Le moteur conserve le comportement historique : les contradictions déjà
    présentes dans ``conversation_context["contradictions"]`` sont reprises,
    normalisées et dédupliquées.

    L'analyse réflexive ne repose jamais sur une interprétation libre des
    libellés. Elle utilise uniquement les métadonnées explicites portées par
    les relations du graphe de reconnaissance :

    - ``contradicts_relation_id`` : identifiant d'une relation contredite ;
    - ``polarity`` : ``positive`` ou ``negative`` ;
    - ``tension`` : ``True`` ou ``potential``.

    Une contradiction explicite et une tension potentielle restent ainsi
    distinguables dans les résultats textuels.
    """

    stage = ReasoningStage.CONTRADICTIONS

    _POSITIVE_POLARITIES = frozenset({"positive", "positif", "+", "1"})
    _NEGATIVE_POLARITIES = frozenset({"negative", "negatif", "négatif", "-", "-1"})
    _POTENTIAL_TENSION_VALUES = frozenset({
        "potential",
        "potentielle",
        "possible",
        "true",
        "1",
    })

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        declared = normalize_string_sequence(
            state.relevant_context.get("contradictions")
        )
        explicit_reflexive = self._detect_explicit_reflexive_contradictions(
            state
        )
        potential_tensions = self._detect_potential_reflexive_tensions(state)

        contradictions = self._deduplicate(
            [*declared, *explicit_reflexive, *potential_tensions]
        )
        state.contradictions.extend(contradictions)

        return {
            "contradictions": contradictions,
            "explicit_reflexive_contradictions": explicit_reflexive,
            "potential_reflexive_tensions": potential_tensions,
        }

    def _detect_explicit_reflexive_contradictions(
        self,
        state: ReasoningExecutionState,
    ) -> list[str]:
        relations = state.recognition_graph.relations
        by_id = {
            relation.relation_id: relation
            for relation in relations
        }
        results: list[str] = []
        seen_pairs: set[tuple[str, str]] = set()

        for relation in relations:
            target_id = normalize_text(
                relation.attributes.get("contradicts_relation_id")
            )
            target = by_id.get(target_id)
            if target is None or target.relation_id == relation.relation_id:
                continue

            pair = tuple(sorted((relation.relation_id, target.relation_id)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            results.append(
                "Contradiction réflexive explicite : "
                f"la relation « {relation.relation_id} » "
                f"({self._describe_relation(relation)}) contredit "
                f"la relation « {target.relation_id} » "
                f"({self._describe_relation(target)})."
            )

        grouped: dict[
            tuple[str, str],
            dict[str, list[RecognitionRelation]],
        ] = defaultdict(lambda: {"positive": [], "negative": []})

        for relation in relations:
            polarity = self._normalize_polarity(
                relation.attributes.get("polarity")
            )
            if polarity is None:
                continue
            grouped[(relation.source_id, relation.target_id)][polarity].append(
                relation
            )

        for (source_id, target_id), polarities in sorted(grouped.items()):
            positives = polarities["positive"]
            negatives = polarities["negative"]
            if not positives or not negatives:
                continue

            positive_ids = ", ".join(
                f"« {relation.relation_id} »"
                for relation in positives
            )
            negative_ids = ", ".join(
                f"« {relation.relation_id} »"
                for relation in negatives
            )
            results.append(
                "Contradiction réflexive explicite : "
                f"les relations {positive_ids} et {negative_ids} déclarent "
                f"des polarités opposées entre « {source_id} » et "
                f"« {target_id} »."
            )

        return self._deduplicate(results)

    def _detect_potential_reflexive_tensions(
        self,
        state: ReasoningExecutionState,
    ) -> list[str]:
        results: list[str] = []

        for relation in state.recognition_graph.relations:
            if not self._is_potential_tension(
                relation.attributes.get("tension")
            ):
                continue
            results.append(
                "Tension réflexive potentielle : "
                f"la relation « {relation.relation_id} » "
                f"({self._describe_relation(relation)}) est explicitement "
                "signalée comme une tension à examiner."
            )

        relation_index = self._build_relation_index(
            state.recognition_graph.relations
        )
        for loop in state.reflexive_loops:
            if not loop.closed:
                continue

            polarities: set[str] = set()
            relation_ids: list[str] = []

            for reflexive_relation in loop.relations:
                candidates = relation_index.get(
                    (
                        reflexive_relation.observer,
                        reflexive_relation.observed,
                        reflexive_relation.relation,
                    ),
                    (),
                )
                for relation in candidates:
                    polarity = self._normalize_polarity(
                        relation.attributes.get("polarity")
                    )
                    if polarity is not None:
                        polarities.add(polarity)
                        relation_ids.append(relation.relation_id)

            if polarities != {"positive", "negative"}:
                continue

            identifiers = ", ".join(
                f"« {relation_id} »"
                for relation_id in dict.fromkeys(relation_ids)
            )
            results.append(
                "Tension réflexive potentielle : "
                f"la boucle fermée contenant {identifiers} associe des "
                "polarités explicites opposées."
            )

        return self._deduplicate(results)

    @staticmethod
    def _build_relation_index(
        relations: Sequence[RecognitionRelation],
    ) -> dict[tuple[str, str, str], tuple[RecognitionRelation, ...]]:
        mutable: dict[
            tuple[str, str, str],
            list[RecognitionRelation],
        ] = defaultdict(list)
        for relation in relations:
            mutable[
                (
                    relation.source_id,
                    relation.target_id,
                    relation.relation_type,
                )
            ].append(relation)
        return {
            key: tuple(value)
            for key, value in mutable.items()
        }

    @classmethod
    def _normalize_polarity(cls, value: Any) -> str | None:
        normalized = normalize_text(value).casefold()
        if normalized in cls._POSITIVE_POLARITIES:
            return "positive"
        if normalized in cls._NEGATIVE_POLARITIES:
            return "negative"
        return None

    @classmethod
    def _is_potential_tension(cls, value: Any) -> bool:
        if value is True:
            return True
        normalized = normalize_text(value).casefold()
        return normalized in cls._POTENTIAL_TENSION_VALUES

    @staticmethod
    def _describe_relation(relation: RecognitionRelation) -> str:
        return (
            f"{relation.source_id} —{relation.relation_type}→ "
            f"{relation.target_id}"
        )

    @staticmethod
    def _deduplicate(values: Sequence[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = normalize_text(value)
            if not normalized:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(normalized)

        return result
