from __future__ import annotations

from collections import deque

from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.models import (
    ExplorationResult,
    GraphPath,
    GraphQuery,
    NeighborhoodResult,
)
from tru_ai.exploration.pathfinder import (
    ExplorationPathfinder,
)


class ExplorationEngine:
    def __init__(
        self,
        indexes: ExplorationIndexes,
    ) -> None:
        self.indexes = indexes
        self.pathfinder = ExplorationPathfinder(indexes)

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        predicates: tuple[str, ...] = (),
        minimum_confidence: float = 0.0,
        include_source_edges: bool = True,
        include_inferred_edges: bool = True,
    ) -> tuple[tuple[str, str], ...]:
        if node_id not in self.indexes.nodes_by_id:
            raise KeyError(node_id)
        if direction not in {"incoming", "outgoing", "both"}:
            raise ValueError("direction invalide")

        predicate_filter = set(predicates)
        pairs = []
        if direction in {"outgoing", "both"}:
            for edge_id in self.indexes.outgoing_edge_ids.get(
                node_id,
                [],
            ):
                edge = self.indexes.edges_by_id[edge_id]
                if self.accept_edge(
                    edge_id,
                    predicate_filter,
                    minimum_confidence,
                    include_source_edges,
                    include_inferred_edges,
                ):
                    pairs.append((edge_id, edge.object_id))
        if direction in {"incoming", "both"}:
            for edge_id in self.indexes.incoming_edge_ids.get(
                node_id,
                [],
            ):
                edge = self.indexes.edges_by_id[edge_id]
                if self.accept_edge(
                    edge_id,
                    predicate_filter,
                    minimum_confidence,
                    include_source_edges,
                    include_inferred_edges,
                ):
                    pairs.append((edge_id, edge.subject_id))
        return tuple(
            sorted(
                set(pairs),
                key=lambda item: (
                    item[1],
                    item[0],
                ),
            )
        )

    def accept_edge(
        self,
        edge_id: str,
        predicates: set[str],
        minimum_confidence: float,
        include_source_edges: bool,
        include_inferred_edges: bool,
    ) -> bool:
        edge = self.indexes.edges_by_id[edge_id]
        inferred = self.indexes.is_inferred_edge(edge)
        if inferred and not include_inferred_edges:
            return False
        if not inferred and not include_source_edges:
            return False
        if predicates and edge.predicate not in predicates:
            return False
        return edge.confidence_average >= minimum_confidence

    def get_neighborhood(
        self,
        node_id: str,
        maximum_depth: int = 2,
        direction: str = "both",
        predicates: tuple[str, ...] = (),
        minimum_confidence: float = 0.0,
        limit: int = 100,
        include_source_edges: bool = True,
        include_inferred_edges: bool = True,
    ) -> NeighborhoodResult:
        if maximum_depth < 0 or maximum_depth > 6:
            raise ValueError(
                "maximum_depth doit être entre 0 et 6."
            )
        visited_nodes = {node_id}
        edge_ids: set[str] = set()
        paths = []
        queue = deque([(node_id, 0)])
        truncated = False

        while queue:
            current_id, depth = queue.popleft()
            if depth >= maximum_depth:
                continue
            for edge_id, neighbor_id in self.get_neighbors(
                current_id,
                direction,
                predicates,
                minimum_confidence,
                include_source_edges,
                include_inferred_edges,
            ):
                edge_ids.add(edge_id)
                if neighbor_id not in visited_nodes:
                    visited_nodes.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))
                if len(edge_ids) > limit:
                    truncated = True
                    break
            if truncated:
                break

        for target_id in sorted(visited_nodes - {node_id}):
            found = self.find_paths(
                node_id,
                target_id,
                predicates,
                maximum_depth,
                minimum_confidence,
                include_source_edges,
                include_inferred_edges,
                1,
            )
            paths.extend(found)

        paths.sort(
            key=lambda path: (
                path.length,
                path.path_id,
            )
        )
        return NeighborhoodResult(
            center_node_id=node_id,
            depth=maximum_depth,
            node_ids=tuple(sorted(visited_nodes)),
            edge_ids=tuple(sorted(edge_ids)[:limit]),
            paths=tuple(paths[:limit]),
            truncated=truncated,
        )

    def find_paths(self, *args, **kwargs):
        return self.pathfinder.find_paths(*args, **kwargs)

    def execute_query(
        self,
        query: GraphQuery,
    ) -> ExplorationResult:
        paths: tuple[GraphPath, ...] = ()
        node_ids: set[str] = set()
        edge_ids: set[str] = set()
        if query.start_node_id and query.end_node_id:
            paths = self.find_paths(
                query.start_node_id,
                query.end_node_id,
                query.predicates,
                query.maximum_depth,
                query.minimum_confidence,
                query.include_source_edges,
                query.include_inferred_edges,
                query.limit,
            )
            for path in paths:
                node_ids.add(path.start_node_id)
                node_ids.add(path.end_node_id)
                for step in path.steps:
                    node_ids.add(step.subject_id)
                    node_ids.add(step.object_id)
                    edge_ids.add(step.edge_id)
        elif query.start_node_id:
            neighborhood = self.get_neighborhood(
                node_id=query.start_node_id,
                maximum_depth=query.maximum_depth,
                direction=query.direction,
                predicates=query.predicates,
                minimum_confidence=query.minimum_confidence,
                limit=query.limit,
                include_source_edges=query.include_source_edges,
                include_inferred_edges=query.include_inferred_edges,
            )
            node_ids.update(neighborhood.node_ids)
            edge_ids.update(neighborhood.edge_ids)
            paths = neighborhood.paths

        explanations = []
        for edge_id in sorted(edge_ids):
            explanation = self.indexes.explanations_by_edge_id.get(
                edge_id
            )
            if explanation is not None:
                explanations.append(explanation.to_dict())

        return ExplorationResult(
            nodes=tuple(
                self.indexes.node_to_dict(node_id)
                for node_id in sorted(node_ids)
            ),
            edges=tuple(
                self.indexes.edge_to_dict(edge_id)
                for edge_id in sorted(edge_ids)
            ),
            paths=tuple(paths),
            explanations=tuple(explanations),
            truncated=False,
        )
