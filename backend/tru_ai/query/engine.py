from __future__ import annotations

from difflib import SequenceMatcher

from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.query.graph_index import GraphIndex
from tru_ai.query.models import (
    NeighborView,
    NodeSearchResult,
    RelationView,
)


class GraphQueryEngine:
    """
    Exécute des recherches déterministes sur
    un GraphIndex.
    """

    def __init__(
        self,
        index: GraphIndex,
    ) -> None:
        self.index = index
        self.normalizer = index.normalizer

    def find_node(
        self,
        query: str,
    ) -> GraphNode | None:
        node_ids = (
            self.index.find_exact_node_ids(
                query
            )
        )

        if not node_ids:
            return None

        return self.index.get_node(
            node_ids[0]
        )

    def require_node(
        self,
        query: str,
    ) -> GraphNode:
        node = self.find_node(query)

        if node is None:
            raise KeyError(
                f"Nœud introuvable : {query}"
            )

        return node

    def search_nodes(
        self,
        query: str,
        limit: int = 20,
    ) -> list[NodeSearchResult]:
        normalized_query = (
            self.normalizer.normalize(query)
        )

        if not normalized_query:
            return []

        results = []

        for node in self.index.graph.nodes:
            candidates = {
                node.label,
                node.normalized_label,
                *node.aliases,
            }

            if node.concept_id:
                candidates.add(node.concept_id)

            normalized_candidates = {
                self.normalizer.normalize(
                    candidate
                )
                for candidate in candidates
                if candidate
            }

            score = max(
                (
                    self.compute_search_score(
                        normalized_query,
                        candidate,
                    )
                    for candidate
                    in normalized_candidates
                ),
                default=0.0,
            )

            if score <= 0:
                continue

            results.append(
                NodeSearchResult(
                    node_id=node.node_id,
                    label=node.label,
                    normalized_label=(
                        node.normalized_label
                    ),
                    node_type=node.node_type,
                    concept_id=node.concept_id,
                    category=node.category,
                    score=round(score, 6),
                )
            )

        results.sort(
            key=lambda result: (
                -result.score,
                result.label.lower(),
                result.node_id,
            )
        )

        return results[:limit]

    def outgoing(
        self,
        query: str,
        predicate: str | None = None,
    ) -> list[RelationView]:
        node = self.require_node(query)

        edges = (
            self.index.get_outgoing_edges(
                node.node_id
            )
        )

        return self.relations_from_edges(
            edges=edges,
            predicate=predicate,
        )

    def incoming(
        self,
        query: str,
        predicate: str | None = None,
    ) -> list[RelationView]:
        node = self.require_node(query)

        edges = (
            self.index.get_incoming_edges(
                node.node_id
            )
        )

        return self.relations_from_edges(
            edges=edges,
            predicate=predicate,
        )

    def neighbors(
        self,
        query: str,
        direction: str = "both",
        predicate: str | None = None,
    ) -> list[NeighborView]:
        node = self.require_node(query)

        if direction not in {
            "incoming",
            "outgoing",
            "both",
        }:
            raise ValueError(
                "La direction doit être "
                "'incoming', 'outgoing' ou 'both'."
            )

        normalized_predicate = (
            self.normalizer.normalize(predicate)
            if predicate
            else None
        )

        neighbors = []

        if direction in {
            "outgoing",
            "both",
        }:
            for edge in (
                self.index.get_outgoing_edges(
                    node.node_id
                )
            ):
                if (
                    normalized_predicate
                    and self.normalizer.normalize(
                        edge.predicate
                    )
                    != normalized_predicate
                ):
                    continue

                object_node = (
                    self.index.get_node(
                        edge.object_id
                    )
                )

                if object_node is None:
                    continue

                neighbors.append(
                    NeighborView(
                        node_id=(
                            object_node.node_id
                        ),
                        label=object_node.label,
                        normalized_label=(
                            object_node
                            .normalized_label
                        ),
                        direction="outgoing",
                        predicate=edge.predicate,
                        edge_id=edge.edge_id,
                        confidence_average=(
                            round(
                                edge
                                .confidence_average,
                                6,
                            )
                        ),
                    )
                )

        if direction in {
            "incoming",
            "both",
        }:
            for edge in (
                self.index.get_incoming_edges(
                    node.node_id
                )
            ):
                if (
                    normalized_predicate
                    and self.normalizer.normalize(
                        edge.predicate
                    )
                    != normalized_predicate
                ):
                    continue

                subject_node = (
                    self.index.get_node(
                        edge.subject_id
                    )
                )

                if subject_node is None:
                    continue

                neighbors.append(
                    NeighborView(
                        node_id=(
                            subject_node.node_id
                        ),
                        label=subject_node.label,
                        normalized_label=(
                            subject_node
                            .normalized_label
                        ),
                        direction="incoming",
                        predicate=edge.predicate,
                        edge_id=edge.edge_id,
                        confidence_average=(
                            round(
                                edge
                                .confidence_average,
                                6,
                            )
                        ),
                    )
                )

        neighbors.sort(
            key=lambda neighbor: (
                neighbor.direction,
                neighbor.predicate,
                neighbor.label.lower(),
                neighbor.node_id,
            )
        )

        return neighbors

    def find_by_predicate(
        self,
        predicate: str,
    ) -> list[RelationView]:
        edges = (
            self.index
            .get_edges_by_predicate(predicate)
        )

        return self.relations_from_edges(
            edges=edges,
        )

    def relations_from_edges(
        self,
        edges: tuple[GraphEdge, ...],
        predicate: str | None = None,
    ) -> list[RelationView]:
        normalized_predicate = (
            self.normalizer.normalize(predicate)
            if predicate
            else None
        )

        relations = []

        for edge in edges:
            if (
                normalized_predicate
                and self.normalizer.normalize(
                    edge.predicate
                )
                != normalized_predicate
            ):
                continue

            subject_node = (
                self.index.get_node(
                    edge.subject_id
                )
            )

            object_node = (
                self.index.get_node(
                    edge.object_id
                )
            )

            if (
                subject_node is None
                or object_node is None
            ):
                continue

            relations.append(
                RelationView(
                    edge_id=edge.edge_id,
                    subject_id=(
                        subject_node.node_id
                    ),
                    subject_label=(
                        subject_node.label
                    ),
                    predicate=edge.predicate,
                    object_id=(
                        object_node.node_id
                    ),
                    object_label=(
                        object_node.label
                    ),
                    occurrence_count=(
                        edge.occurrence_count
                    ),
                    confidence_average=round(
                        edge.confidence_average,
                        6,
                    ),
                )
            )

        relations.sort(
            key=lambda relation: (
                relation.predicate,
                relation.subject_label.lower(),
                relation.object_label.lower(),
                relation.edge_id,
            )
        )

        return relations

    @staticmethod
    def compute_search_score(
        query: str,
        candidate: str,
    ) -> float:
        if not candidate:
            return 0.0

        if candidate == query:
            return 1.0

        if candidate.startswith(query):
            return 0.95

        if query in candidate:
            return 0.90

        similarity = SequenceMatcher(
            None,
            query,
            candidate,
        ).ratio()

        if similarity < 0.45:
            return 0.0

        return similarity