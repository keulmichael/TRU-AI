from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState
from tru_ai.cognitive.reasoning.models import (
    RecognitionGraph,
    RecognitionRelation,
    ReflexiveGraph,
    ReflexiveLoop,
    ReflexiveRelation,
    ReasoningStage,
    ReasoningStep,
)


class ReflexivityEngine:
    """Construit la réflexivité à partir des relations explicites du graphe."""

    stage = ReasoningStage.REFLEXIVITY
    _MAX_CYCLE_LENGTH = 12

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        graph = state.recognition_graph
        loops_by_relation_ids = self._detect_loops(graph)
        relation_ids_in_loops = {
            relation_id
            for relation_ids in loops_by_relation_ids
            for relation_id in relation_ids
        }

        reflexive_relations = tuple(
            self._to_reflexive_relation(
                relation,
                belongs_to_loop=relation.relation_id in relation_ids_in_loops,
            )
            for relation in graph.relations
        )
        relations_by_id = {
            source.relation_id: reflexive
            for source, reflexive in zip(
                graph.relations,
                reflexive_relations,
                strict=True,
            )
        }
        reflexive_loops = tuple(
            ReflexiveLoop(
                relations=tuple(
                    relations_by_id[relation_id]
                    for relation_id in relation_ids
                ),
                closed=True,
            )
            for relation_ids in loops_by_relation_ids
        )
        reflexive_graph = ReflexiveGraph(
            relations=reflexive_relations,
            loops=reflexive_loops,
        )

        state.reflexive_graph = reflexive_graph
        state.reflexive_relations.extend(reflexive_relations)
        state.reflexive_loops.extend(reflexive_loops)

        return {
            "reflexive_graph": reflexive_graph.to_dict(),
            "reflexive_relations": [
                relation.to_dict() for relation in reflexive_relations
            ],
            "reflexive_loops": [loop.to_dict() for loop in reflexive_loops],
        }

    @staticmethod
    def _to_reflexive_relation(
        relation: RecognitionRelation,
        *,
        belongs_to_loop: bool,
    ) -> ReflexiveRelation:
        if relation.source_id == relation.target_id:
            recognition_level = 3
        elif belongs_to_loop:
            recognition_level = 2
        else:
            recognition_level = 1

        return ReflexiveRelation(
            observer=relation.source_id,
            observed=relation.target_id,
            relation=relation.relation_type,
            recognition_level=recognition_level,
            confidence=ReflexivityEngine._normalize_confidence(
                relation.attributes.get("confidence")
            ),
        )

    @staticmethod
    def _normalize_confidence(value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            numeric = float(value)
            if 0.0 <= numeric <= 1.0:
                return numeric
        return None

    def _detect_loops(
        self,
        graph: RecognitionGraph,
    ) -> tuple[tuple[str, ...], ...]:
        loops: dict[
            tuple[str, ...],
            tuple[tuple[str, ...], tuple[str, ...]],
        ] = {}

        for relation in graph.relations:
            if relation.source_id == relation.target_id:
                key = (relation.source_id,)
                loops.setdefault(
                    key,
                    ((relation.source_id,), (relation.relation_id,)),
                )

        adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for relation in graph.relations:
            if relation.source_id != relation.target_id:
                adjacency[relation.source_id].append(
                    (relation.target_id, relation.relation_id)
                )
        for source_id in adjacency:
            adjacency[source_id].sort(key=lambda item: (item[0], item[1]))

        for start in sorted(adjacency):
            self._walk_cycles(
                start=start,
                current=start,
                adjacency=adjacency,
                path_nodes=(start,),
                path_relations=(),
                loops=loops,
            )

        ordered = sorted(
            loops.values(),
            key=lambda item: (len(item[0]), item[0], item[1]),
        )
        return tuple(relation_ids for _, relation_ids in ordered)

    def _walk_cycles(
        self,
        *,
        start: str,
        current: str,
        adjacency: Mapping[str, list[tuple[str, str]]],
        path_nodes: tuple[str, ...],
        path_relations: tuple[str, ...],
        loops: dict[
            tuple[str, ...],
            tuple[tuple[str, ...], tuple[str, ...]],
        ],
    ) -> None:
        for target_id, relation_id in adjacency.get(current, []):
            if target_id == start and len(path_nodes) >= 2:
                canonical_nodes, rotation = self._canonical_cycle(path_nodes)
                relation_ids = (*path_relations, relation_id)
                canonical_relations = (
                    relation_ids[rotation:] + relation_ids[:rotation]
                )
                loops.setdefault(
                    canonical_nodes,
                    (canonical_nodes, canonical_relations),
                )
                continue

            if (
                target_id in path_nodes
                or len(path_nodes) >= self._MAX_CYCLE_LENGTH
            ):
                continue

            self._walk_cycles(
                start=start,
                current=target_id,
                adjacency=adjacency,
                path_nodes=(*path_nodes, target_id),
                path_relations=(*path_relations, relation_id),
                loops=loops,
            )

    @staticmethod
    def _canonical_cycle(
        node_ids: tuple[str, ...],
    ) -> tuple[tuple[str, ...], int]:
        rotations = [
            (node_ids[index:] + node_ids[:index], index)
            for index in range(len(node_ids))
        ]
        return min(rotations, key=lambda item: item[0])
