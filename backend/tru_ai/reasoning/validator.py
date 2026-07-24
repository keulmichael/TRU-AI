from __future__ import annotations

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.inference.models import (
    InferenceTrace,
    InferredEdge,
    canonical_edge_key,
)
from tru_ai.reasoning.explainer import (
    ReasoningExplainer,
)
from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
    ReasoningResult,
    ReasoningValidationReport,
    make_explanation_id,
    make_proof_node_id,
    make_reasoning_step_id,
)


class ReasoningValidator:
    def validate(
        self,
        graph: KnowledgeGraph,
        inferred_edges: tuple[InferredEdge, ...],
        traces: tuple[InferenceTrace, ...],
        result: ReasoningResult,
    ) -> ReasoningValidationReport:
        report = ReasoningValidationReport()
        graph_edges_by_id = {
            edge.edge_id: edge
            for edge in graph.edges
        }
        inferred_ids = {
            edge.edge_id
            for edge in inferred_edges
        }
        explanation_ids = {
            explanation.inferred_edge_id
            for explanation in result.explanations
        }
        proof_trees_by_id = {
            tree.node_id: tree
            for tree in result.proof_trees
        }

        if inferred_ids - explanation_ids:
            report.add_error(
                "Arêtes inférées non expliquées : "
                f"{sorted(inferred_ids - explanation_ids)}"
            )

        if (
            result.explained_edge_count
            != len(result.explanations)
        ):
            report.add_error(
                "Compteur d'explications incohérent."
            )

        for tree in result.proof_trees:
            self.validate_tree(
                report,
                tree,
                graph_edges_by_id,
                (),
            )

        for explanation in result.explanations:
            self.validate_explanation(
                report=report,
                explanation=explanation,
                proof_trees_by_id=(
                    proof_trees_by_id
                ),
                inferred_ids=inferred_ids,
                graph_edges_by_id=(
                    graph_edges_by_id
                ),
                graph=graph,
                inferred_edges=inferred_edges,
                traces=traces,
            )

        return report

    def validate_tree(
        self,
        report: ReasoningValidationReport,
        node: ProofTreeNode,
        graph_edges_by_id: dict,
        visited: tuple[str, ...],
    ) -> None:
        if node.node_id in visited:
            report.add_error(
                "Cycle dans l'arbre de preuve : "
                f"{node.node_id}"
            )
            return

        edge = graph_edges_by_id.get(
            node.edge_id
        )
        if edge is None:
            report.add_error(
                "Arête d'arbre absente : "
                f"{node.edge_id}"
            )
            return

        edge_key = canonical_edge_key(
            edge.subject_id,
            edge.predicate,
            edge.object_id,
        )
        if node.edge_key != edge_key:
            report.add_error(
                "Clé d'arbre incohérente : "
                f"{node.node_id}"
            )

        child_ids = tuple(
            child.node_id
            for child in node.children
        )
        expected_id = make_proof_node_id(
            edge_id=node.edge_id,
            edge_key=node.edge_key,
            node_type=node.node_type,
            rule_id=node.rule_id,
            depth=node.depth,
            child_node_ids=child_ids,
            root=node.node_id.startswith(
                "proof-tree-"
            ),
        )

        if node.node_id != expected_id:
            report.add_error(
                "Identifiant d'arbre "
                "non déterministe : "
                f"{node.node_id}"
            )

        if node.node_type == "source_fact":
            if node.rule_id is not None:
                report.add_error(
                    "Fait source avec règle : "
                    f"{node.node_id}"
                )
            if node.children:
                report.add_error(
                    "Fait source avec enfants : "
                    f"{node.node_id}"
                )
            if node.depth != 0:
                report.add_error(
                    "Profondeur de source invalide : "
                    f"{node.node_id}"
                )
        elif node.node_type == "inferred_fact":
            if not node.rule_id:
                report.add_error(
                    "Fait inféré sans règle : "
                    f"{node.node_id}"
                )
            if not node.children:
                report.add_error(
                    "Fait inféré sans prémisse : "
                    f"{node.node_id}"
                )
        else:
            report.add_error(
                "Type de nœud de preuve invalide : "
                f"{node.node_id}"
            )

        for child in node.children:
            if child.depth >= node.depth:
                report.add_error(
                    "Profondeur enfant incohérente : "
                    f"{child.node_id}"
                )
            self.validate_tree(
                report,
                child,
                graph_edges_by_id,
                (
                    *visited,
                    node.node_id,
                ),
            )

    def validate_explanation(
        self,
        report: ReasoningValidationReport,
        explanation: ReasoningExplanation,
        proof_trees_by_id: dict[str, ProofTreeNode],
        inferred_ids: set[str],
        graph_edges_by_id: dict,
        graph: KnowledgeGraph,
        inferred_edges: tuple[InferredEdge, ...],
        traces: tuple[InferenceTrace, ...],
    ) -> None:
        if (
            explanation.inferred_edge_id
            not in inferred_ids
        ):
            report.add_error(
                "Explication sans arête inférée : "
                f"{explanation.explanation_id}"
            )

        tree = proof_trees_by_id.get(
            explanation.proof_tree_id
        )
        if tree is None:
            report.add_error(
                "Arbre de preuve absent : "
                f"{explanation.proof_tree_id}"
            )
            return

        if (
            tree.edge_id
            != explanation.inferred_edge_id
        ):
            report.add_error(
                "Conclusion finale incohérente : "
                f"{explanation.explanation_id}"
            )

        if (
            tree.edge_key
            != explanation.conclusion_edge_key
        ):
            report.add_error(
                "Clé de conclusion incohérente : "
                f"{explanation.explanation_id}"
            )

        expected_explanation_id = (
            make_explanation_id(
                inferred_edge_id=(
                    explanation.inferred_edge_id
                ),
                conclusion_edge_key=(
                    explanation
                    .conclusion_edge_key
                ),
                proof_tree_id=(
                    explanation.proof_tree_id
                ),
                rule_ids=(
                    explanation.rule_ids
                ),
            )
        )

        if (
            explanation.explanation_id
            != expected_explanation_id
        ):
            report.add_error(
                "Identifiant d'explication "
                "non déterministe : "
                f"{explanation.explanation_id}"
            )

        for index, step in enumerate(
            explanation.steps,
            start=1,
        ):
            if step.step_number != index:
                report.add_error(
                    "Ordre d'étapes invalide : "
                    f"{step.step_id}"
                )

            expected_step_id = (
                make_reasoning_step_id(
                    edge_id=step.edge_id,
                    role=step.role,
                    depth=step.depth,
                )
            )
            if step.step_id != expected_step_id:
                report.add_error(
                    "Identifiant d'étape "
                    "non déterministe : "
                    f"{step.step_id}"
                )

            if step.edge_id not in graph_edges_by_id:
                report.add_error(
                    "Étape avec arête absente : "
                    f"{step.edge_id}"
                )

        depths = [
            step.depth
            for step in explanation.steps
        ]
        if depths != sorted(depths):
            report.add_error(
                "Étapes hors ordre de profondeur : "
                f"{explanation.explanation_id}"
            )

        expected_text = ReasoningExplainer(
            graph=graph,
            inferred_edges=inferred_edges,
            traces=traces,
        ).build_text(
            proof_tree=tree,
            steps=explanation.steps,
        )
        if (
            explanation.deterministic_text
            != expected_text
        ):
            report.add_error(
                "Texte déterministe incohérent : "
                f"{explanation.explanation_id}"
            )

    @staticmethod
    def compare_results(
        first: ReasoningResult,
        second: ReasoningResult,
    ) -> ReasoningValidationReport:
        report = ReasoningValidationReport()

        if first.to_dict() != second.to_dict():
            report.add_error(
                "Résultats reasoning instables."
            )

        return report
