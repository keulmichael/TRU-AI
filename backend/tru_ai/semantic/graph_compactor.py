from __future__ import annotations

import hashlib

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.semantic.models import (
    ResolutionResult,
)


class SemanticGraphCompactor:
    def compact(
        self,
        graph: KnowledgeGraph,
        resolution: ResolutionResult,
    ) -> KnowledgeGraph:
        source_nodes = {
            node.node_id: node
            for node in graph.nodes
        }

        resolved_nodes: dict[
            str,
            GraphNode,
        ] = {}

        for node in graph.nodes:
            canonical_id = resolution.canonical_id(
                node.node_id
            )

            if canonical_id not in resolved_nodes:
                canonical_source = source_nodes[
                    canonical_id
                ]

                resolved_nodes[canonical_id] = (
                    GraphNode(
                        node_id=canonical_source.node_id,
                        label=canonical_source.label,
                        normalized_label=(
                            canonical_source
                            .normalized_label
                        ),
                        node_type=(
                            canonical_source.node_type
                        ),
                        concept_id=(
                            canonical_source.concept_id
                        ),
                        category=(
                            canonical_source.category
                        ),
                        aliases=set(
                            canonical_source.aliases
                        ),
                        source_sentence_ids=set(
                            canonical_source
                            .source_sentence_ids
                        ),
                        occurrence_count=(
                            canonical_source
                            .occurrence_count
                        ),
                    )
                )

            if node.node_id == canonical_id:
                continue

            canonical_node = resolved_nodes[
                canonical_id
            ]

            canonical_node.aliases.update(
                node.aliases
            )
            canonical_node.aliases.add(
                node.label
            )
            canonical_node.source_sentence_ids.update(
                node.source_sentence_ids
            )
            canonical_node.occurrence_count += (
                node.occurrence_count
            )

        resolved_edges: dict[
            tuple[str, str, str],
            GraphEdge,
        ] = {}

        for edge in graph.edges:
            subject_id = resolution.canonical_id(
                edge.subject_id
            )

            object_id = resolution.canonical_id(
                edge.object_id
            )

            key = (
                subject_id,
                edge.predicate,
                object_id,
            )

            if key not in resolved_edges:
                edge_id = self.make_edge_id(
                    subject_id,
                    edge.predicate,
                    object_id,
                )

                resolved_edges[key] = GraphEdge(
                    edge_id=edge_id,
                    subject_id=subject_id,
                    predicate=edge.predicate,
                    object_id=object_id,
                    relation_ids=set(
                        edge.relation_ids
                    ),
                    proposition_ids=set(
                        edge.proposition_ids
                    ),
                    source_sentence_ids=set(
                        edge.source_sentence_ids
                    ),
                    pattern_ids=set(
                        edge.pattern_ids
                    ),
                    extraction_methods=set(
                        edge.extraction_methods
                    ),
                    occurrence_count=(
                        edge.occurrence_count
                    ),
                    confidence_sum=(
                        edge.confidence_sum
                    ),
                    confidence_max=(
                        edge.confidence_max
                    ),
                )

                continue

            target_edge = resolved_edges[key]

            target_edge.relation_ids.update(
                edge.relation_ids
            )
            target_edge.proposition_ids.update(
                edge.proposition_ids
            )
            target_edge.source_sentence_ids.update(
                edge.source_sentence_ids
            )
            target_edge.pattern_ids.update(
                edge.pattern_ids
            )
            target_edge.extraction_methods.update(
                edge.extraction_methods
            )
            target_edge.occurrence_count += (
                edge.occurrence_count
            )
            target_edge.confidence_sum += (
                edge.confidence_sum
            )
            target_edge.confidence_max = max(
                target_edge.confidence_max,
                edge.confidence_max,
            )

        return KnowledgeGraph(
            nodes=tuple(
                sorted(
                    resolved_nodes.values(),
                    key=lambda node: node.node_id,
                )
            ),
            edges=tuple(
                sorted(
                    resolved_edges.values(),
                    key=lambda edge: edge.edge_id,
                )
            ),
        )

    @staticmethod
    def make_edge_id(
        subject_id: str,
        predicate: str,
        object_id: str,
    ) -> str:
        payload = (
            f"{subject_id}|"
            f"{predicate}|"
            f"{object_id}"
        )

        digest = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()[:16]

        return f"edge-{digest}"