from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass

from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.graph.resolver import EntityResolver
from tru_ai.relations.models import Relation


@dataclass(frozen=True)
class KnowledgeGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def node_index(
        self,
    ) -> dict[str, GraphNode]:
        return {
            node.node_id: node
            for node in self.nodes
        }

    def edge_index(
        self,
    ) -> dict[str, GraphEdge]:
        return {
            edge.edge_id: edge
            for edge in self.edges
        }

    def build_adjacency(
        self,
    ) -> dict[str, dict]:
        outgoing: dict[
            str,
            list[dict],
        ] = defaultdict(list)

        incoming: dict[
            str,
            list[dict],
        ] = defaultdict(list)

        for edge in self.edges:
            outgoing[edge.subject_id].append(
                {
                    "edge_id": edge.edge_id,
                    "predicate": edge.predicate,
                    "object_id": edge.object_id,
                    "occurrence_count": (
                        edge.occurrence_count
                    ),
                    "confidence": round(
                        edge.confidence_average,
                        6,
                    ),
                }
            )

            incoming[edge.object_id].append(
                {
                    "edge_id": edge.edge_id,
                    "predicate": edge.predicate,
                    "subject_id": edge.subject_id,
                    "occurrence_count": (
                        edge.occurrence_count
                    ),
                    "confidence": round(
                        edge.confidence_average,
                        6,
                    ),
                }
            )

        adjacency = {}

        for node in self.nodes:
            adjacency[node.node_id] = {
                "outgoing": sorted(
                    outgoing.get(
                        node.node_id,
                        [],
                    ),
                    key=lambda item: (
                        item["predicate"],
                        item["object_id"],
                    ),
                ),
                "incoming": sorted(
                    incoming.get(
                        node.node_id,
                        [],
                    ),
                    key=lambda item: (
                        item["predicate"],
                        item["subject_id"],
                    ),
                ),
            }

        return adjacency


class KnowledgeGraphBuilder:
    """
    Transforme les relations extraites en nœuds
    et arêtes dédupliqués.
    """

    def __init__(
        self,
        resolver: EntityResolver | None = None,
    ) -> None:
        self.resolver = (
            resolver or EntityResolver()
        )

    def build(
        self,
        relations: list[Relation],
    ) -> KnowledgeGraph:
        nodes: dict[str, GraphNode] = {}
        edges: dict[str, GraphEdge] = {}

        for relation in relations:
            subject_node = self.resolver.resolve(
                relation.subject_label
            )

            object_node = self.resolver.resolve(
                relation.object_label
            )

            self.merge_node(
                nodes=nodes,
                incoming_node=subject_node,
                source_label=relation.subject_label,
                sentence_id=relation.sentence_id,
            )

            self.merge_node(
                nodes=nodes,
                incoming_node=object_node,
                source_label=relation.object_label,
                sentence_id=relation.sentence_id,
            )

            edge_id = self.build_edge_id(
                subject_id=subject_node.node_id,
                predicate=relation.predicate,
                object_id=object_node.node_id,
            )

            edge = edges.get(edge_id)

            if edge is None:
                edge = GraphEdge(
                    edge_id=edge_id,
                    subject_id=subject_node.node_id,
                    predicate=relation.predicate,
                    object_id=object_node.node_id,
                )

                edges[edge_id] = edge

            edge.register_relation(
                relation_id=relation.relation_id,
                proposition_id=(
                    relation.proposition_id
                ),
                sentence_id=relation.sentence_id,
                pattern_id=relation.pattern_id,
                extraction_method=(
                    relation.extraction_method
                ),
                confidence=relation.confidence,
            )

        ordered_nodes = tuple(
            sorted(
                nodes.values(),
                key=lambda node: node.node_id,
            )
        )

        ordered_edges = tuple(
            sorted(
                edges.values(),
                key=lambda edge: edge.edge_id,
            )
        )

        return KnowledgeGraph(
            nodes=ordered_nodes,
            edges=ordered_edges,
        )

    @staticmethod
    def merge_node(
        nodes: dict[str, GraphNode],
        incoming_node: GraphNode,
        source_label: str,
        sentence_id: str,
    ) -> None:
        existing_node = nodes.get(
            incoming_node.node_id
        )

        if existing_node is None:
            existing_node = incoming_node
            nodes[incoming_node.node_id] = (
                existing_node
            )

        existing_node.register_occurrence(
            label=source_label,
            sentence_id=sentence_id,
        )

    @staticmethod
    def build_edge_id(
        subject_id: str,
        predicate: str,
        object_id: str,
    ) -> str:
        raw_identifier = (
            f"{subject_id}|{predicate}|{object_id}"
        )

        digest = hashlib.sha256(
            raw_identifier.encode("utf-8")
        ).hexdigest()[:16]

        return f"edge-{digest}"