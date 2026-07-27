from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState
from tru_ai.cognitive.reasoning.models import (
    RecognitionCompleteness,
    RecognitionGap,
    RecognitionGapType,
    RecognitionMeaning,
    RecognitionMeaningGraph,
    RecognitionStability,
    ReasoningStage,
    ReasoningStep,
)


class RecognitionMeaningEngine:
    """Calcule ce qui est reconnu à partir des structures explicites.

    Le moteur n'attribue aucune intention psychologique. Les objets reconnus
    proviennent des relations du graphe. Les objets recherchés, évités ou
    explicitement non reconnus ne sont retenus que lorsqu'un attribut du nœud
    le déclare. Les écarts structurels signalent seulement l'absence de
    relation entrante dans les données disponibles.
    """

    stage = ReasoningStage.RECOGNITION_MEANING

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        graph = state.recognition_graph
        reflexive_relations = tuple(state.reflexive_relations)

        incoming: dict[str, list[Any]] = defaultdict(list)
        relation_index = {
            (
                relation.source_id,
                relation.target_id,
                relation.relation_type,
            ): relation
            for relation in graph.relations
        }
        for relation in graph.relations:
            incoming[relation.target_id].append(relation)

        loop_pairs = {
            (relation.observer, relation.observed, relation.relation)
            for loop in state.reflexive_loops
            if loop.closed
            for relation in loop.relations
        }

        meanings: list[RecognitionMeaning] = []
        for object_id in sorted(incoming):
            relations = incoming[object_id]
            matching_reflexive = [
                relation
                for relation in reflexive_relations
                if relation.observed == object_id
            ]
            observers = tuple(sorted({r.source_id for r in relations}))
            relation_types = tuple(sorted({r.relation_type for r in relations}))
            evidence_ids = tuple(sorted({r.relation_id for r in relations}))
            recognition_level = max(
                (r.recognition_level for r in matching_reflexive),
                default=0,
            )
            reciprocal = any(
                (
                    relation.target_id,
                    relation.source_id,
                    relation.relation_type,
                )
                in relation_index
                for relation in relations
            )
            stable = any(
                relation.source_id == relation.target_id
                or (
                    relation.source_id,
                    relation.target_id,
                    relation.relation_type,
                )
                in loop_pairs
                for relation in relations
            )
            confidence_values = [
                relation.confidence
                for relation in matching_reflexive
                if relation.confidence is not None
            ]
            confidence = (
                round(sum(confidence_values) / len(confidence_values), 6)
                if confidence_values
                else None
            )
            meanings.append(
                RecognitionMeaning(
                    object_id=object_id,
                    observers=observers,
                    relation_types=relation_types,
                    recognition_level=recognition_level,
                    reciprocal=reciprocal,
                    stable=stable,
                    evidence_relation_ids=evidence_ids,
                    confidence=confidence,
                )
            )

        node_by_id = {node.node_id: node for node in graph.nodes}
        eligible_ids = {
            node.node_id
            for node in graph.nodes
            if node.kind != "claim"
        }
        gaps: list[RecognitionGap] = []
        for object_id in sorted(eligible_ids):
            node = node_by_id[object_id]
            attributes = node.attributes
            status = str(attributes.get("recognition_status", "")).strip().casefold()

            if object_id not in incoming:
                gaps.append(
                    RecognitionGap(
                        object_id=object_id,
                        gap_type=RecognitionGapType.STRUCTURAL,
                        description=(
                            "Aucune relation entrante de reconnaissance n'est "
                            "présente pour cet objet dans le graphe fourni."
                        ),
                    )
                )

            explicit_markers = (
                ("unrecognized", RecognitionGapType.EXPLICIT_UNRECOGNIZED),
                ("non_reconnu", RecognitionGapType.EXPLICIT_UNRECOGNIZED),
                ("searched", RecognitionGapType.SEARCHED),
                ("recherche", RecognitionGapType.SEARCHED),
                ("avoided", RecognitionGapType.AVOIDED),
                ("evite", RecognitionGapType.AVOIDED),
            )
            for marker, gap_type in explicit_markers:
                flag_name = {
                    RecognitionGapType.SEARCHED: "searched",
                    RecognitionGapType.AVOIDED: "avoided",
                    RecognitionGapType.EXPLICIT_UNRECOGNIZED: "recognized",
                }[gap_type]
                declared = status == marker
                if gap_type is RecognitionGapType.EXPLICIT_UNRECOGNIZED:
                    declared = declared or attributes.get(flag_name) is False
                else:
                    declared = declared or attributes.get(flag_name) is True
                if not declared:
                    continue
                gaps.append(
                    RecognitionGap(
                        object_id=object_id,
                        gap_type=gap_type,
                        description=(
                            "Le statut de reconnaissance est explicitement "
                            f"déclaré « {gap_type.value} »."
                        ),
                        evidence=(f"recognition_status={status}",) if status else (),
                    )
                )

        recognized_ids = set(incoming).intersection(eligible_ids)
        total_objects = len(eligible_ids)
        completeness_score = (
            len(recognized_ids) / total_objects
            if total_objects
            else 0.0
        )
        stable_count = sum(1 for meaning in meanings if meaning.stable)
        stability_score = (
            stable_count / len(meanings)
            if meanings
            else 0.0
        )

        completeness = RecognitionCompleteness(
            recognized_objects=len(recognized_ids),
            total_objects=total_objects,
            score=round(completeness_score, 6),
        )
        stability = RecognitionStability(
            stable_objects=stable_count,
            total_recognized_objects=len(meanings),
            score=round(stability_score, 6),
        )
        meaning_graph = RecognitionMeaningGraph(
            meanings=tuple(meanings),
            gaps=tuple(gaps),
            completeness=completeness,
            stability=stability,
        )

        state.recognition_meaning_graph = meaning_graph
        state.recognition_meanings.extend(meanings)
        state.recognition_gaps.extend(gaps)

        return {
            "recognition_meaning_graph": meaning_graph.to_dict(),
            "recognition_meanings": [item.to_dict() for item in meanings],
            "recognition_gaps": [item.to_dict() for item in gaps],
            "recognition_completeness": completeness.to_dict(),
            "recognition_stability": stability.to_dict(),
        }
