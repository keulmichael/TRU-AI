from __future__ import annotations

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.inference.models import (
    InferenceTrace,
    InferredEdge,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)
from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
    ReasoningStep,
    make_explanation_id,
    make_reasoning_step_id,
)


class ReasoningExplainer:
    def __init__(
        self,
        graph: KnowledgeGraph,
        inferred_edges: tuple[InferredEdge, ...],
        traces: tuple[InferenceTrace, ...],
        registry: InferenceRuleRegistry | None = None,
    ) -> None:
        self.graph = graph
        self.inferred_edges_by_id = {
            edge.edge_id: edge
            for edge in inferred_edges
        }
        self.traces_by_edge_id: dict[
            str,
            list[InferenceTrace],
        ] = {}
        self.registry = (
            registry
            or InferenceRuleRegistry.default()
        )
        self.node_labels = {
            node.node_id: node.label
            for node in graph.nodes
        }
        self.edges_by_id = {
            edge.edge_id: edge
            for edge in graph.edges
        }

        for trace in traces:
            self.traces_by_edge_id.setdefault(
                trace.inferred_edge_id,
                [],
            ).append(trace)

        for trace_list in (
            self.traces_by_edge_id.values()
        ):
            trace_list.sort(
                key=lambda trace: trace.inference_id
            )

    def explain(
        self,
        proof_tree: ProofTreeNode,
    ) -> ReasoningExplanation:
        inferred_edge = (
            self.inferred_edges_by_id[
                proof_tree.edge_id
            ]
        )
        traces = self.traces_by_edge_id.get(
            proof_tree.edge_id,
            [],
        )
        rule_ids = tuple(
            sorted(
                {
                    trace.rule_id
                    for trace in traces
                }
            )
        )
        steps = self.build_steps(proof_tree)
        text = self.build_text(
            proof_tree=proof_tree,
            steps=steps,
        )
        explanation_id = make_explanation_id(
            inferred_edge_id=(
                inferred_edge.edge_id
            ),
            conclusion_edge_key=(
                proof_tree.edge_key
            ),
            proof_tree_id=proof_tree.node_id,
            rule_ids=rule_ids,
        )

        return ReasoningExplanation(
            explanation_id=explanation_id,
            inferred_edge_id=(
                inferred_edge.edge_id
            ),
            conclusion_edge_key=(
                proof_tree.edge_key
            ),
            rule_ids=rule_ids,
            steps=steps,
            proof_tree_id=proof_tree.node_id,
            maximum_depth=proof_tree.depth,
            confidence=proof_tree.confidence,
            deterministic_text=text,
        )

    def build_steps(
        self,
        proof_tree: ProofTreeNode,
    ) -> tuple[ReasoningStep, ...]:
        ordered_nodes = self.postorder(
            proof_tree
        )
        steps: list[ReasoningStep] = []

        for index, node in enumerate(
            ordered_nodes,
            start=1,
        ):
            role = (
                "conclusion"
                if node.node_type
                == "inferred_fact"
                else "premise"
            )
            edge = self.edges_by_id[node.edge_id]
            step_id = make_reasoning_step_id(
                edge_id=node.edge_id,
                role=role,
                depth=node.depth,
            )
            steps.append(
                ReasoningStep(
                    step_id=step_id,
                    step_number=index,
                    edge_id=node.edge_id,
                    edge_key=node.edge_key,
                    role=role,
                    depth=node.depth,
                    confidence=node.confidence,
                    source_sentence_ids=tuple(
                        sorted(
                            edge.source_sentence_ids
                        )
                    ),
                )
            )

        return tuple(steps)

    def postorder(
        self,
        node: ProofTreeNode,
    ) -> tuple[ProofTreeNode, ...]:
        nodes: list[ProofTreeNode] = []

        for child in sorted(
            node.children,
            key=lambda item: (
                item.depth,
                item.edge_key,
                item.edge_id,
            ),
        ):
            nodes.extend(
                self.postorder(child)
            )

        nodes.append(node)

        return tuple(nodes)

    def build_text(
        self,
        proof_tree: ProofTreeNode,
        steps: tuple[ReasoningStep, ...],
    ) -> str:
        rule_name = proof_tree.rule_id

        if proof_tree.rule_id:
            rule = self.registry.get(
                proof_tree.rule_id
            )
            if rule is not None:
                rule_name = rule.name

        premise_steps = [
            step
            for step in steps
            if step.role == "premise"
        ]

        lines = [
            "Conclusion:",
            self.format_edge_key(
                proof_tree.edge_key
            ),
            "",
            "Rule:",
            rule_name or "",
            "",
            "Premises:",
        ]

        if premise_steps:
            for index, step in enumerate(
                premise_steps,
                start=1,
            ):
                lines.append(
                    f"{index}. "
                    f"{self.format_edge_key(step.edge_key)}"
                )
        else:
            lines.append("None")

        lines.extend(
            [
                "",
                "Depth:",
                str(proof_tree.depth),
                "",
                "Confidence:",
                f"{proof_tree.confidence:.6f}",
            ]
        )

        return "\n".join(lines)

    def format_edge_key(
        self,
        edge_key: tuple[str, str, str],
    ) -> str:
        subject_id, predicate, object_id = edge_key

        return (
            f"{self.node_labels.get(subject_id, subject_id)} "
            f"{predicate} "
            f"{self.node_labels.get(object_id, object_id)}"
        )

    def explain_all(
        self,
        proof_trees: tuple[ProofTreeNode, ...],
    ) -> tuple[ReasoningExplanation, ...]:
        return tuple(
            sorted(
                (
                    self.explain(tree)
                    for tree in proof_trees
                ),
                key=lambda explanation: (
                    explanation.inferred_edge_id
                ),
            )
        )
