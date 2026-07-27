from __future__ import annotations

from collections import defaultdict

from tru_ai.extraction.lexical_normalizer import LexicalNormalizer
from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge
from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
)


class ExplorationIndexes:
    def __init__(
        self,
        graph: KnowledgeGraph,
        explanations: tuple[ReasoningExplanation, ...] = (),
        proof_trees: tuple[ProofTreeNode, ...] = (),
        normalizer: LexicalNormalizer | None = None,
    ) -> None:
        self.graph = graph
        self.normalizer = normalizer or LexicalNormalizer()
        self.nodes_by_id = {
            node.node_id: node
            for node in graph.nodes
        }
        self.edges_by_id = {
            edge.edge_id: edge
            for edge in graph.edges
        }
        self.node_ids_by_label: dict[
            str,
            list[str],
        ] = defaultdict(list)
        self.outgoing_edge_ids: dict[
            str,
            list[str],
        ] = defaultdict(list)
        self.incoming_edge_ids: dict[
            str,
            list[str],
        ] = defaultdict(list)
        self.edge_ids_by_predicate: dict[
            str,
            list[str],
        ] = defaultdict(list)
        self.edge_ids_by_key: dict[
            tuple[str, str, str],
            str,
        ] = {}
        self.explanations_by_edge_id = {
            explanation.inferred_edge_id: explanation
            for explanation in explanations
        }
        self.proof_trees_by_edge_id = {
            proof_tree.edge_id: proof_tree
            for proof_tree in proof_trees
        }
        self.build()

    def build(self) -> None:
        for node in self.graph.nodes:
            labels = {
                node.node_id,
                node.label,
                node.normalized_label,
                *node.aliases,
            }
            for label in labels:
                normalized = self.normalizer.normalize(
                    label
                )
                if normalized:
                    self.node_ids_by_label[
                        normalized
                    ].append(node.node_id)

        for edge in self.graph.edges:
            self.outgoing_edge_ids[
                edge.subject_id
            ].append(edge.edge_id)
            self.incoming_edge_ids[
                edge.object_id
            ].append(edge.edge_id)
            self.edge_ids_by_predicate[
                edge.predicate
            ].append(edge.edge_id)
            self.edge_ids_by_key[
                (
                    edge.subject_id,
                    edge.predicate,
                    edge.object_id,
                )
            ] = edge.edge_id

        for mapping in (
            self.node_ids_by_label,
            self.outgoing_edge_ids,
            self.incoming_edge_ids,
            self.edge_ids_by_predicate,
        ):
            for key in list(mapping):
                mapping[key] = sorted(
                    set(mapping[key])
                )

    def is_inferred_edge(
        self,
        edge: GraphEdge,
    ) -> bool:
        return (
            "deterministic_inference"
            in edge.extraction_methods
            or edge.edge_id
            in self.explanations_by_edge_id
        )

    def edge_explanation_id(
        self,
        edge_id: str,
    ) -> str | None:
        explanation = (
            self.explanations_by_edge_id.get(
                edge_id
            )
        )
        if explanation is None:
            return None
        return explanation.explanation_id

    def node_to_dict(
        self,
        node_id: str,
    ) -> dict:
        node = self.nodes_by_id[node_id]
        return node.to_dict()

    def edge_to_dict(
        self,
        edge_id: str,
    ) -> dict:
        edge = self.edges_by_id[edge_id]
        record = edge.to_dict()
        inferred = self.is_inferred_edge(edge)
        record["inferred"] = inferred
        record["explanation_id"] = (
            self.edge_explanation_id(edge.edge_id)
        )
        return record

    def search_nodes(
        self,
        search: str | None,
        limit: int,
        offset: int = 0,
    ) -> tuple[dict, ...]:
        normalized = (
            self.normalizer.normalize(search)
            if search
            else ""
        )
        records = []
        for node in self.graph.nodes:
            candidates = {
                node.node_id,
                node.label,
                node.normalized_label,
                *node.aliases,
            }
            normalized_candidates = {
                self.normalizer.normalize(value)
                for value in candidates
                if value
            }
            if normalized and not any(
                normalized in candidate
                for candidate
                in normalized_candidates
            ):
                continue
            records.append(node.to_dict())

        records.sort(
            key=lambda item: (
                item["label"].lower(),
                item["node_id"],
            )
        )
        return tuple(records[offset: offset + limit])

    def to_files(self) -> dict[str, dict]:
        return {
            "node_index": {
                key: value
                for key, value
                in sorted(
                    self.node_ids_by_label.items()
                )
            },
            "predicate_index": {
                key: value
                for key, value
                in sorted(
                    self.edge_ids_by_predicate.items()
                )
            },
            "outgoing_index": {
                key: value
                for key, value
                in sorted(
                    self.outgoing_edge_ids.items()
                )
            },
            "incoming_index": {
                key: value
                for key, value
                in sorted(
                    self.incoming_edge_ids.items()
                )
            },
            "edge_explanation_index": {
                edge_id: explanation.explanation_id
                for edge_id, explanation
                in sorted(
                    self.explanations_by_edge_id.items()
                )
            },
        }
