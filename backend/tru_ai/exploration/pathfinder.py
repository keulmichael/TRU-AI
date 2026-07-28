from __future__ import annotations

from collections import deque

from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.models import (
    GraphPath,
    GraphPathStep,
    make_path_id,
)


class ExplorationPathfinder:
    def __init__(
        self,
        indexes: ExplorationIndexes,
    ) -> None:
        self.indexes = indexes

    def find_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        predicates: tuple[str, ...] = (),
        maximum_depth: int = 4,
        minimum_confidence: float = 0.0,
        include_source_edges: bool = True,
        include_inferred_edges: bool = True,
        limit: int = 20,
    ) -> tuple[GraphPath, ...]:
        if start_node_id not in self.indexes.nodes_by_id:
            raise KeyError(start_node_id)
        if end_node_id not in self.indexes.nodes_by_id:
            raise KeyError(end_node_id)
        if maximum_depth < 0 or maximum_depth > 8:
            raise ValueError(
                "maximum_depth doit être entre 0 et 8."
            )
        if limit < 1:
            raise ValueError("limit doit être positif.")

        queue: deque[tuple[str, tuple[str, ...], tuple[str, ...]]] = deque(
            [(start_node_id, tuple(), (start_node_id,))]
        )
        paths: list[GraphPath] = []

        while queue and len(paths) < limit * 4:
            current_id, edge_ids, node_ids = (
                queue.popleft()
            )
            if len(edge_ids) >= maximum_depth:
                continue

            for edge_id, neighbor_id in self.iter_edges(
                current_id,
                predicates,
                minimum_confidence,
                include_source_edges,
                include_inferred_edges,
            ):
                if neighbor_id in node_ids:
                    continue
                next_edge_ids = (
                    *edge_ids,
                    edge_id,
                )
                next_node_ids = (
                    *node_ids,
                    neighbor_id,
                )
                if neighbor_id == end_node_id:
                    paths.append(
                        self.build_path(
                            start_node_id,
                            end_node_id,
                            next_edge_ids,
                        )
                    )
                else:
                    queue.append(
                        (
                            neighbor_id,
                            next_edge_ids,
                            next_node_ids,
                        )
                    )

        paths.sort(
            key=lambda path: (
                path.length,
                -path.minimum_confidence,
                path.inferred_edge_count,
                path.path_id,
            )
        )
        return tuple(paths[:limit])

    def iter_edges(
        self,
        node_id: str,
        predicates: tuple[str, ...],
        minimum_confidence: float,
        include_source_edges: bool,
        include_inferred_edges: bool,
    ) -> tuple[tuple[str, str], ...]:
        predicate_filter = set(predicates)
        candidates = []
        for edge_id in self.indexes.outgoing_edge_ids.get(
            node_id,
            [],
        ):
            edge = self.indexes.edges_by_id[edge_id]
            inferred = self.indexes.is_inferred_edge(edge)
            if inferred and not include_inferred_edges:
                continue
            if not inferred and not include_source_edges:
                continue
            if (
                predicate_filter
                and edge.predicate not in predicate_filter
            ):
                continue
            if edge.confidence_average < minimum_confidence:
                continue
            candidates.append((edge_id, edge.object_id))
        return tuple(
            sorted(
                candidates,
                key=lambda item: (
                    item[1],
                    item[0],
                ),
            )
        )

    def build_path(
        self,
        start_node_id: str,
        end_node_id: str,
        edge_ids: tuple[str, ...],
    ) -> GraphPath:
        steps = []
        confidences = []
        inferred_count = 0
        for position, edge_id in enumerate(
            edge_ids,
            start=1,
        ):
            edge = self.indexes.edges_by_id[edge_id]
            inferred = self.indexes.is_inferred_edge(edge)
            if inferred:
                inferred_count += 1
            confidence = round(
                edge.confidence_average,
                6,
            )
            confidences.append(confidence)
            steps.append(
                GraphPathStep(
                    position=position,
                    edge_id=edge.edge_id,
                    subject_id=edge.subject_id,
                    predicate=edge.predicate,
                    object_id=edge.object_id,
                    direction="outgoing",
                    inferred=inferred,
                    confidence=confidence,
                    explanation_id=(
                        self.indexes.edge_explanation_id(
                            edge.edge_id
                        )
                    ),
                )
            )

        path_id = make_path_id(
            start_node_id,
            end_node_id,
            edge_ids,
        )

        return GraphPath(
            path_id=path_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            steps=tuple(steps),
            length=len(steps),
            minimum_confidence=min(
                confidences,
                default=0.0,
            ),
            inferred_edge_count=inferred_count,
        )
