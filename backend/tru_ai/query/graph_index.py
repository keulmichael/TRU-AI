from __future__ import annotations

from collections import defaultdict

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)


class GraphIndex:
    """
    Index en mémoire pour accélérer les recherches
    dans le graphe de connaissances.
    """

    def __init__(
        self,
        graph: KnowledgeGraph,
        normalizer: LexicalNormalizer | None = None,
    ) -> None:
        self.graph = graph

        self.normalizer = (
            normalizer or LexicalNormalizer()
        )

        self.nodes_by_id: dict[
            str,
            GraphNode,
        ] = {}

        self.edges_by_id: dict[
            str,
            GraphEdge,
        ] = {}

        self.node_ids_by_label: dict[
            str,
            set[str],
        ] = defaultdict(set)

        self.node_ids_by_alias: dict[
            str,
            set[str],
        ] = defaultdict(set)

        self.edge_ids_by_predicate: dict[
            str,
            set[str],
        ] = defaultdict(set)

        self.outgoing_edge_ids: dict[
            str,
            list[str],
        ] = defaultdict(list)

        self.incoming_edge_ids: dict[
            str,
            list[str],
        ] = defaultdict(list)

        self.build()

    def build(self) -> None:
        for node in self.graph.nodes:
            self.nodes_by_id[node.node_id] = node

            normalized_label = (
                self.normalizer.normalize(
                    node.normalized_label
                    or node.label
                )
            )

            self.node_ids_by_label[
                normalized_label
            ].add(node.node_id)

            aliases = set(node.aliases)
            aliases.add(node.label)

            if node.concept_id:
                aliases.add(node.concept_id)

            for alias in aliases:
                normalized_alias = (
                    self.normalizer.normalize(alias)
                )

                if normalized_alias:
                    self.node_ids_by_alias[
                        normalized_alias
                    ].add(node.node_id)

        for edge in self.graph.edges:
            self.edges_by_id[edge.edge_id] = edge

            normalized_predicate = (
                self.normalizer.normalize(
                    edge.predicate
                )
            )

            self.edge_ids_by_predicate[
                normalized_predicate
            ].add(edge.edge_id)

            self.outgoing_edge_ids[
                edge.subject_id
            ].append(edge.edge_id)

            self.incoming_edge_ids[
                edge.object_id
            ].append(edge.edge_id)

        for edge_ids in (
            self.outgoing_edge_ids.values()
        ):
            edge_ids.sort()

        for edge_ids in (
            self.incoming_edge_ids.values()
        ):
            edge_ids.sort()

    def find_exact_node_ids(
        self,
        query: str,
    ) -> tuple[str, ...]:
        normalized_query = (
            self.normalizer.normalize(query)
        )

        node_ids = set()

        node_ids.update(
            self.node_ids_by_label.get(
                normalized_query,
                set(),
            )
        )

        node_ids.update(
            self.node_ids_by_alias.get(
                normalized_query,
                set(),
            )
        )

        if query in self.nodes_by_id:
            node_ids.add(query)

        return tuple(sorted(node_ids))

    def get_node(
        self,
        node_id: str,
    ) -> GraphNode | None:
        return self.nodes_by_id.get(node_id)

    def get_edge(
        self,
        edge_id: str,
    ) -> GraphEdge | None:
        return self.edges_by_id.get(edge_id)

    def get_outgoing_edges(
        self,
        node_id: str,
    ) -> tuple[GraphEdge, ...]:
        return tuple(
            self.edges_by_id[edge_id]
            for edge_id in (
                self.outgoing_edge_ids.get(
                    node_id,
                    [],
                )
            )
        )

    def get_incoming_edges(
        self,
        node_id: str,
    ) -> tuple[GraphEdge, ...]:
        return tuple(
            self.edges_by_id[edge_id]
            for edge_id in (
                self.incoming_edge_ids.get(
                    node_id,
                    [],
                )
            )
        )

    def get_edges_by_predicate(
        self,
        predicate: str,
    ) -> tuple[GraphEdge, ...]:
        normalized_predicate = (
            self.normalizer.normalize(predicate)
        )

        edge_ids = (
            self.edge_ids_by_predicate.get(
                normalized_predicate,
                set(),
            )
        )

        return tuple(
            self.edges_by_id[edge_id]
            for edge_id in sorted(edge_ids)
        )

    def to_dict(self) -> dict:
        return {
            "node_ids_by_label": {
                label: sorted(node_ids)
                for label, node_ids
                in sorted(
                    self.node_ids_by_label.items()
                )
            },
            "node_ids_by_alias": {
                alias: sorted(node_ids)
                for alias, node_ids
                in sorted(
                    self.node_ids_by_alias.items()
                )
            },
            "edge_ids_by_predicate": {
                predicate: sorted(edge_ids)
                for predicate, edge_ids
                in sorted(
                    self.edge_ids_by_predicate.items()
                )
            },
            "outgoing_edge_ids": {
                node_id: edge_ids
                for node_id, edge_ids
                in sorted(
                    self.outgoing_edge_ids.items()
                )
            },
            "incoming_edge_ids": {
                node_id: edge_ids
                for node_id, edge_ids
                in sorted(
                    self.incoming_edge_ids.items()
                )
            },
        }