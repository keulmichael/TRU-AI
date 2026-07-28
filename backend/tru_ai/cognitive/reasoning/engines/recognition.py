from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_text,
)
from tru_ai.cognitive.reasoning.models import (
    RecognitionGraph,
    RecognitionNode,
    RecognitionPattern,
    RecognitionPatternType,
    RecognitionRelation,
    ReasoningStage,
    ReasoningStep,
)


class RecognitionEngine:
    """
    Construit un graphe relationnel explicite puis en détecte les motifs.

    Le moteur ne déduit aucune relation sémantique à partir du seul texte.
    Il analyse uniquement les nœuds et relations fournis explicitement dans
    ``conversation_context["recognition_graph"]``. Les claims sont ajoutés
    comme nœuds isolés afin de rendre leur présence observable sans inventer
    de liens entre eux.
    """

    stage = ReasoningStage.RECOGNITION

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        graph = self._build_graph(state)
        patterns = self._detect_patterns(graph)

        state.recognition_graph = graph
        state.recognition_patterns.extend(patterns)

        return {
            "recognition_graph": graph.to_dict(),
            "recognition_patterns": [
                pattern.to_dict()
                for pattern in patterns
            ],
        }

    def _build_graph(
        self,
        state: ReasoningExecutionState,
    ) -> RecognitionGraph:
        raw_graph = state.conversation_context.get("recognition_graph", {})
        if not isinstance(raw_graph, Mapping):
            raw_graph = {}

        nodes = self._normalize_nodes(raw_graph.get("nodes", ()))
        relations = self._normalize_relations(
            raw_graph.get("relations", ()),
            known_node_ids={node.node_id for node in nodes},
        )

        existing_ids = {node.node_id for node in nodes}
        for index, claim in enumerate(state.claims, start=1):
            node_id = f"claim:{index}"
            if node_id in existing_ids:
                continue
            nodes.append(
                RecognitionNode(
                    node_id=node_id,
                    label=claim.text,
                    kind="claim",
                    attributes={"truth_status": claim.status.value},
                )
            )
            existing_ids.add(node_id)

        return RecognitionGraph(
            nodes=tuple(nodes),
            relations=tuple(relations),
        )

    @staticmethod
    def _normalize_nodes(value: Any) -> list[RecognitionNode]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            return []

        nodes: list[RecognitionNode] = []
        seen_ids: set[str] = set()

        for item in value:
            if not isinstance(item, Mapping):
                continue

            node_id = normalize_text(item.get("node_id") or item.get("id"))
            label = normalize_text(item.get("label"))
            kind = normalize_text(item.get("kind")) or "concept"
            attributes = item.get("attributes", {})

            if not node_id or not label or node_id in seen_ids:
                continue
            if not isinstance(attributes, Mapping):
                attributes = {}

            nodes.append(
                RecognitionNode(
                    node_id=node_id,
                    label=label,
                    kind=kind,
                    attributes=dict(attributes),
                )
            )
            seen_ids.add(node_id)

        return nodes

    @staticmethod
    def _normalize_relations(
        value: Any,
        *,
        known_node_ids: set[str],
    ) -> list[RecognitionRelation]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            return []

        relations: list[RecognitionRelation] = []
        seen_ids: set[str] = set()

        for index, item in enumerate(value, start=1):
            if not isinstance(item, Mapping):
                continue

            source_id = normalize_text(item.get("source_id") or item.get("source"))
            target_id = normalize_text(item.get("target_id") or item.get("target"))
            relation_type = (
                normalize_text(item.get("relation_type") or item.get("type"))
                or "related_to"
            )
            relation_id = (
                normalize_text(item.get("relation_id") or item.get("id"))
                or f"relation:{index}"
            )
            attributes = item.get("attributes", {})

            if (
                not source_id
                or not target_id
                or source_id not in known_node_ids
                or target_id not in known_node_ids
                or relation_id in seen_ids
            ):
                continue
            if not isinstance(attributes, Mapping):
                attributes = {}

            relations.append(
                RecognitionRelation(
                    relation_id=relation_id,
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    attributes=dict(attributes),
                )
            )
            seen_ids.add(relation_id)

        return relations

    def _detect_patterns(
        self,
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        patterns: list[RecognitionPattern] = []
        patterns.extend(self._detect_repetitions(graph))
        patterns.extend(self._detect_fixed_points(graph))
        patterns.extend(self._detect_declared_relations(graph))
        patterns.extend(self._detect_symmetries(graph))
        patterns.extend(self._detect_bifurcations(graph))
        patterns.extend(self._detect_cycles(graph))
        return self._deduplicate_patterns(patterns)

    @staticmethod
    def _detect_repetitions(
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        labels = [node.label.casefold() for node in graph.nodes]
        counts = Counter(labels)
        patterns: list[RecognitionPattern] = []

        for normalized_label, count in counts.items():
            if count < 2:
                continue
            matching = tuple(
                node
                for node in graph.nodes
                if node.label.casefold() == normalized_label
            )
            patterns.append(
                RecognitionPattern(
                    pattern_type=RecognitionPatternType.REPETITION,
                    description=(
                        f"Le même élément « {matching[0].label} » apparaît "
                        f"{count} fois dans le graphe."
                    ),
                    evidence=tuple(node.label for node in matching),
                    node_ids=tuple(node.node_id for node in matching),
                )
            )

        return patterns

    @staticmethod
    def _detect_fixed_points(
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        return [
            RecognitionPattern(
                pattern_type=RecognitionPatternType.FIXED_POINT,
                description=(
                    f"La relation « {relation.relation_type} » revient "
                    f"sur le même nœud « {relation.source_id} »."
                ),
                evidence=(relation.relation_type,),
                node_ids=(relation.source_id,),
                relation_ids=(relation.relation_id,),
            )
            for relation in graph.relations
            if relation.source_id == relation.target_id
        ]

    @staticmethod
    def _detect_declared_relations(
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        mapping = {
            "inversion": RecognitionPatternType.INVERSION,
            "inverse": RecognitionPatternType.INVERSION,
            "transformation": RecognitionPatternType.TRANSFORMATION,
            "transforms_into": RecognitionPatternType.TRANSFORMATION,
        }
        patterns: list[RecognitionPattern] = []

        for relation in graph.relations:
            pattern_type = mapping.get(relation.relation_type.casefold())
            if pattern_type is None:
                continue
            patterns.append(
                RecognitionPattern(
                    pattern_type=pattern_type,
                    description=(
                        f"La relation explicite « {relation.relation_type} » "
                        f"relie « {relation.source_id} » à "
                        f"« {relation.target_id} »."
                    ),
                    evidence=(relation.relation_type,),
                    node_ids=(relation.source_id, relation.target_id),
                    relation_ids=(relation.relation_id,),
                )
            )

        return patterns

    @staticmethod
    def _detect_symmetries(
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        relation_index = {
            (relation.source_id, relation.target_id, relation.relation_type.casefold()): relation
            for relation in graph.relations
            if relation.source_id != relation.target_id
        }
        patterns: list[RecognitionPattern] = []
        seen_pairs: set[tuple[str, str, str]] = set()

        for key, relation in relation_index.items():
            source_id, target_id, relation_type = key
            reverse = relation_index.get((target_id, source_id, relation_type))
            first_id, second_id = sorted((source_id, target_id))
            canonical = (first_id, second_id, relation_type)
            if reverse is None or canonical in seen_pairs:
                continue
            seen_pairs.add(canonical)
            patterns.append(
                RecognitionPattern(
                    pattern_type=RecognitionPatternType.SYMMETRY,
                    description=(
                        f"Une relation réciproque de type « {relation.relation_type} » "
                        f"relie « {source_id} » et « {target_id} »."
                    ),
                    evidence=(relation.relation_type,),
                    node_ids=(source_id, target_id),
                    relation_ids=(relation.relation_id, reverse.relation_id),
                )
            )

        return patterns

    @staticmethod
    def _detect_bifurcations(
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        outgoing: dict[str, list[RecognitionRelation]] = defaultdict(list)
        for relation in graph.relations:
            if relation.source_id != relation.target_id:
                outgoing[relation.source_id].append(relation)

        patterns: list[RecognitionPattern] = []
        for source_id, relations in outgoing.items():
            targets = tuple(dict.fromkeys(r.target_id for r in relations))
            if len(targets) < 2:
                continue
            patterns.append(
                RecognitionPattern(
                    pattern_type=RecognitionPatternType.BIFURCATION,
                    description=(
                        f"Le nœud « {source_id} » mène vers "
                        f"{len(targets)} nœuds distincts."
                    ),
                    evidence=targets,
                    node_ids=(source_id, *targets),
                    relation_ids=tuple(r.relation_id for r in relations),
                )
            )

        return patterns

    def _detect_cycles(
        self,
        graph: RecognitionGraph,
    ) -> list[RecognitionPattern]:
        adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for relation in graph.relations:
            if relation.source_id != relation.target_id:
                adjacency[relation.source_id].append(
                    (relation.target_id, relation.relation_id)
                )

        cycles: dict[tuple[str, ...], tuple[tuple[str, ...], tuple[str, ...]]] = {}
        for start in adjacency:
            self._walk_cycles(
                start=start,
                current=start,
                adjacency=adjacency,
                path_nodes=(start,),
                path_relations=(),
                cycles=cycles,
            )

        return [
            RecognitionPattern(
                pattern_type=RecognitionPatternType.CYCLE,
                description=(
                    "Un cycle relationnel explicite relie successivement "
                    + " → ".join((*node_ids, node_ids[0]))
                    + "."
                ),
                evidence=node_ids,
                node_ids=node_ids,
                relation_ids=relation_ids,
            )
            for node_ids, relation_ids in cycles.values()
        ]

    def _walk_cycles(
        self,
        *,
        start: str,
        current: str,
        adjacency: Mapping[str, list[tuple[str, str]]],
        path_nodes: tuple[str, ...],
        path_relations: tuple[str, ...],
        cycles: dict[tuple[str, ...], tuple[tuple[str, ...], tuple[str, ...]]],
    ) -> None:
        for target, relation_id in adjacency.get(current, []):
            if target == start and len(path_nodes) >= 2:
                canonical = self._canonical_cycle(path_nodes)
                cycles.setdefault(
                    canonical,
                    (path_nodes, (*path_relations, relation_id)),
                )
                continue
            if target in path_nodes or len(path_nodes) >= 12:
                continue
            self._walk_cycles(
                start=start,
                current=target,
                adjacency=adjacency,
                path_nodes=(*path_nodes, target),
                path_relations=(*path_relations, relation_id),
                cycles=cycles,
            )

    @staticmethod
    def _canonical_cycle(node_ids: tuple[str, ...]) -> tuple[str, ...]:
        rotations = [
            node_ids[index:] + node_ids[:index]
            for index in range(len(node_ids))
        ]
        return min(rotations)

    @staticmethod
    def _deduplicate_patterns(
        patterns: list[RecognitionPattern],
    ) -> list[RecognitionPattern]:
        result: list[RecognitionPattern] = []
        seen: set[tuple[Any, ...]] = set()

        for pattern in patterns:
            key = (
                pattern.pattern_type,
                tuple(sorted(pattern.node_ids)),
                tuple(sorted(pattern.relation_ids)),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(pattern)

        return result
