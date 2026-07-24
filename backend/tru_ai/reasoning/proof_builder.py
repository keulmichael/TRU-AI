from __future__ import annotations

from collections import defaultdict

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge
from tru_ai.inference.models import (
    InferenceTrace,
    InferredEdge,
    canonical_edge_key,
)
from tru_ai.reasoning.models import (
    ProofTreeNode,
    make_proof_node_id,
)


class ProofBuilder:
    def __init__(
        self,
        graph: KnowledgeGraph,
        inferred_edges: tuple[InferredEdge, ...],
        traces: tuple[InferenceTrace, ...],
    ) -> None:
        self.graph = graph
        self.inferred_edges = inferred_edges
        self.traces = traces
        self.edges_by_id: dict[str, GraphEdge] = {
            edge.edge_id: edge
            for edge in graph.edges
        }
        self.inferred_edges_by_id = {
            edge.edge_id: edge
            for edge in inferred_edges
        }
        self.traces_by_edge_id: dict[
            str,
            list[InferenceTrace],
        ] = defaultdict(list)

        for trace in traces:
            self.traces_by_edge_id[
                trace.inferred_edge_id
            ].append(trace)

        for trace_list in (
            self.traces_by_edge_id.values()
        ):
            trace_list.sort(
                key=self.trace_rank
            )

    @staticmethod
    def trace_rank(
        trace: InferenceTrace,
    ) -> tuple:
        return (
            trace.inference_depth,
            -trace.confidence,
            trace.rule_id,
            trace.inference_id,
        )

    def build_all(
        self,
    ) -> tuple[
        tuple[ProofTreeNode, ...],
        tuple[str, ...],
    ]:
        proof_trees: list[ProofTreeNode] = []
        unexplained_edge_ids: list[str] = []

        for edge in sorted(
            self.inferred_edges,
            key=lambda item: item.edge_id,
        ):
            try:
                proof_trees.append(
                    self.build_for_edge(
                        edge.edge_id
                    )
                )
            except ValueError:
                unexplained_edge_ids.append(
                    edge.edge_id
                )

        return (
            tuple(
                sorted(
                    proof_trees,
                    key=lambda tree: tree.edge_id,
                )
            ),
            tuple(
                sorted(
                    unexplained_edge_ids
                )
            ),
        )

    def build_for_edge(
        self,
        edge_id: str,
    ) -> ProofTreeNode:
        return self.build_node(
            edge_id=edge_id,
            visited=(),
            root=True,
        )

    def build_node(
        self,
        edge_id: str,
        visited: tuple[str, ...],
        *,
        root: bool = False,
    ) -> ProofTreeNode:
        if edge_id in visited:
            raise ValueError(
                "Cycle détecté dans l'arbre "
                f"de preuve : {edge_id}"
            )

        edge = self.edges_by_id.get(edge_id)

        if edge is None:
            raise ValueError(
                "Arête absente : "
                f"{edge_id}"
            )

        edge_key = canonical_edge_key(
            edge.subject_id,
            edge.predicate,
            edge.object_id,
        )

        inferred_edge = (
            self.inferred_edges_by_id.get(
                edge_id
            )
        )

        if inferred_edge is None:
            return self.build_source_node(
                edge=edge,
                edge_key=edge_key,
                root=root,
            )

        trace = self.select_trace(edge_id)
        children = tuple(
            sorted(
                (
                    self.build_node(
                        premise_edge_id,
                        (
                            *visited,
                            edge_id,
                        ),
                    )
                    for premise_edge_id
                    in trace.premise_edge_ids
                ),
                key=lambda child: (
                    child.depth,
                    child.edge_key,
                    child.edge_id,
                ),
            )
        )

        child_node_ids = tuple(
            child.node_id
            for child in children
        )

        node_id = make_proof_node_id(
            edge_id=edge.edge_id,
            edge_key=edge_key,
            node_type="inferred_fact",
            rule_id=trace.rule_id,
            depth=trace.inference_depth,
            child_node_ids=child_node_ids,
            root=root,
        )

        return ProofTreeNode(
            node_id=node_id,
            edge_id=edge.edge_id,
            edge_key=edge_key,
            node_type="inferred_fact",
            rule_id=trace.rule_id,
            confidence=edge.confidence_max,
            depth=trace.inference_depth,
            children=children,
        )

    def build_source_node(
        self,
        edge: GraphEdge,
        edge_key,
        *,
        root: bool = False,
    ) -> ProofTreeNode:
        node_id = make_proof_node_id(
            edge_id=edge.edge_id,
            edge_key=edge_key,
            node_type="source_fact",
            rule_id=None,
            depth=0,
            child_node_ids=(),
            root=root,
        )

        return ProofTreeNode(
            node_id=node_id,
            edge_id=edge.edge_id,
            edge_key=edge_key,
            node_type="source_fact",
            rule_id=None,
            confidence=edge.confidence_max,
            depth=0,
            children=(),
        )

    def select_trace(
        self,
        inferred_edge_id: str,
    ) -> InferenceTrace:
        traces = self.traces_by_edge_id.get(
            inferred_edge_id,
            [],
        )

        if not traces:
            raise ValueError(
                "Trace absente pour l'arête "
                f"inférée : {inferred_edge_id}"
            )

        return traces[0]
