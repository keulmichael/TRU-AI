from __future__ import annotations

from collections import Counter

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.inference.models import (
    EdgeKey,
    InferenceResult,
    InferenceTrace,
    InferenceValidationReport,
    InferredEdge,
    canonical_edge_key,
    make_inference_id,
    make_inferred_edge_id,
)
from tru_ai.inference.rule import (
    apply_inverse_rule,
    apply_symmetry_rule,
    apply_transitivity_rule,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)


class InferenceValidator:
    def __init__(
        self,
        registry: InferenceRuleRegistry | None = None,
        max_depth: int = 2,
    ) -> None:
        self.registry = (
            registry
            or InferenceRuleRegistry.default()
        )
        self.max_depth = max_depth

    def validate(
        self,
        graph: KnowledgeGraph,
        result: InferenceResult,
    ) -> InferenceValidationReport:
        report = InferenceValidationReport()

        for error in self.registry.validate():
            report.add_error(error)

        node_ids = {
            node.node_id
            for node in graph.nodes
        }

        source_edges_by_id = {
            edge.edge_id: edge
            for edge in graph.edges
        }

        source_edges_by_key = {
            canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            ): edge
            for edge in graph.edges
        }

        inferred_edges_by_id = {
            edge.edge_id: edge
            for edge in result.inferred_edges
        }

        inferred_edges_by_key = {
            canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            ): edge
            for edge in result.inferred_edges
        }

        self.validate_inferred_edges(
            report=report,
            node_ids=node_ids,
            source_edges_by_key=(
                source_edges_by_key
            ),
            inferred_edges=result.inferred_edges,
        )

        self.validate_traces(
            report=report,
            result=result,
            source_edges_by_id=(
                source_edges_by_id
            ),
            inferred_edges_by_id=(
                inferred_edges_by_id
            ),
            inferred_edges_by_key=(
                inferred_edges_by_key
            ),
        )

        return report

    def validate_inferred_edges(
        self,
        report: InferenceValidationReport,
        node_ids: set[str],
        source_edges_by_key: dict[
            EdgeKey,
            object,
        ],
        inferred_edges: tuple[InferredEdge, ...],
    ) -> None:
        edge_keys = [
            canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            )
            for edge in inferred_edges
        ]

        key_counts = Counter(edge_keys)

        for edge_key, count in key_counts.items():
            if count > 1:
                report.add_error(
                    "Arête inférée dupliquée : "
                    f"{edge_key}"
                )

        for edge in inferred_edges:
            edge_key = canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            )

            if edge.subject_id not in node_ids:
                report.add_error(
                    "Sujet absent pour l'arête "
                    f"inférée {edge.edge_id}."
                )

            if edge.object_id not in node_ids:
                report.add_error(
                    "Objet absent pour l'arête "
                    f"inférée {edge.edge_id}."
                )

            if edge.subject_id == edge.object_id:
                report.add_error(
                    "Self-loop inféré interdit : "
                    f"{edge.edge_id}"
                )

            if edge_key in source_edges_by_key:
                report.add_error(
                    "Arête inférée déjà présente "
                    "dans les sources : "
                    f"{edge.edge_id}"
                )

            if edge.inference_depth < 1:
                report.add_error(
                    "Profondeur inférée invalide : "
                    f"{edge.edge_id}"
                )

            if (
                edge.inference_depth
                > self.max_depth
            ):
                report.add_error(
                    "Profondeur inférée supérieure "
                    "au maximum : "
                    f"{edge.edge_id}"
                )

            if not (
                0.0
                <= edge.confidence_max
                <= 1.0
            ):
                report.add_error(
                    "Confiance maximale invalide : "
                    f"{edge.edge_id}"
                )

            if edge.confidence_sum < edge.confidence_max:
                report.add_error(
                    "Somme de confiance incohérente : "
                    f"{edge.edge_id}"
                )

            if edge.occurrence_count < 1:
                report.add_error(
                    "Nombre d'occurrences invalide : "
                    f"{edge.edge_id}"
                )

            expected_edge_id = make_inferred_edge_id(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            )

            if edge.edge_id != expected_edge_id:
                report.add_error(
                    "Identifiant d'arête inférée "
                    "non déterministe : "
                    f"{edge.edge_id}"
                )

    def validate_traces(
        self,
        report: InferenceValidationReport,
        result: InferenceResult,
        source_edges_by_id: dict,
        inferred_edges_by_id: dict[
            str,
            InferredEdge,
        ],
        inferred_edges_by_key: dict[
            EdgeKey,
            InferredEdge,
        ],
    ) -> None:
        all_edges_by_id = {
            **source_edges_by_id,
            **inferred_edges_by_id,
        }

        for trace in result.traces:
            rule = self.registry.get(
                trace.rule_id
            )

            if rule is None:
                report.add_error(
                    "Règle absente : "
                    f"{trace.rule_id}"
                )
                continue

            inferred_edge = (
                inferred_edges_by_id.get(
                    trace.inferred_edge_id
                )
            )

            if inferred_edge is None:
                report.add_error(
                    "Trace liée à une arête "
                    "inférée absente : "
                    f"{trace.inference_id}"
                )
                continue

            premise_edges = []

            for premise_edge_id in (
                trace.premise_edge_ids
            ):
                premise_edge = all_edges_by_id.get(
                    premise_edge_id
                )

                if premise_edge is None:
                    report.add_error(
                        "Prémisse absente : "
                        f"{premise_edge_id}"
                    )
                    continue

                premise_edges.append(
                    premise_edge
                )

            if len(premise_edges) != len(
                trace.premise_edge_ids
            ):
                continue

            expected_keys = tuple(
                sorted(
                    canonical_edge_key(
                        edge.subject_id,
                        edge.predicate,
                        edge.object_id,
                    )
                    for edge in premise_edges
                )
            )

            if tuple(
                sorted(
                    trace.premise_edge_keys
                )
            ) != expected_keys:
                report.add_error(
                    "Clé de prémisse incohérente : "
                    f"{trace.inference_id}"
                )
                continue

            self.validate_trace_depth(
                report,
                trace,
            )

            self.validate_trace_confidence(
                report,
                trace,
            )

            self.validate_trace_id(
                report=report,
                trace=trace,
                inferred_edge=inferred_edge,
            )

            ordered_premise_edges = (
                self.order_premise_edges(
                    rule=rule,
                    trace=trace,
                    premise_edges=premise_edges,
                )
            )

            self.validate_trace_conclusion(
                report=report,
                trace=trace,
                rule=rule,
                premise_edges=(
                    ordered_premise_edges
                ),
                inferred_edge=inferred_edge,
                inferred_edges_by_key=(
                    inferred_edges_by_key
                ),
            )

    @staticmethod
    def order_premise_edges(
        rule,
        trace: InferenceTrace,
        premise_edges: list,
    ) -> list:
        if rule.rule_type != "transitivity":
            return premise_edges

        first_key = canonical_edge_key(
            trace.variable_bindings.get(
                "target_subject_id",
                "",
            ),
            trace.variable_bindings.get(
                "source_predicate",
                "",
            ),
            trace.variable_bindings.get(
                "middle_node_id",
                "",
            ),
        )

        second_key = canonical_edge_key(
            trace.variable_bindings.get(
                "middle_node_id",
                "",
            ),
            trace.variable_bindings.get(
                "source_predicate",
                "",
            ),
            trace.variable_bindings.get(
                "target_object_id",
                "",
            ),
        )

        edges_by_key = {
            canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            ): edge
            for edge in premise_edges
        }

        if (
            first_key in edges_by_key
            and second_key in edges_by_key
        ):
            return [
                edges_by_key[first_key],
                edges_by_key[second_key],
            ]

        return premise_edges

    def validate_trace_depth(
        self,
        report: InferenceValidationReport,
        trace: InferenceTrace,
    ) -> None:
        if trace.inference_depth < 1:
            report.add_error(
                "Profondeur de trace invalide : "
                f"{trace.inference_id}"
            )

        if trace.inference_depth > self.max_depth:
            report.add_error(
                "Profondeur de trace supérieure "
                "au maximum : "
                f"{trace.inference_id}"
            )

    @staticmethod
    def validate_trace_confidence(
        report: InferenceValidationReport,
        trace: InferenceTrace,
    ) -> None:
        if not (
            0.0
            <= trace.confidence
            <= 1.0
        ):
            report.add_error(
                "Confiance de trace invalide : "
                f"{trace.inference_id}"
            )

    @staticmethod
    def validate_trace_id(
        report: InferenceValidationReport,
        trace: InferenceTrace,
        inferred_edge: InferredEdge,
    ) -> None:
        expected_id = make_inference_id(
            rule_id=trace.rule_id,
            premise_edge_ids=(
                trace.premise_edge_ids
            ),
            premise_edge_keys=(
                trace.premise_edge_keys
            ),
            subject_id=inferred_edge.subject_id,
            predicate=inferred_edge.predicate,
            object_id=inferred_edge.object_id,
            inference_depth=(
                trace.inference_depth
            ),
            variable_bindings=(
                trace.variable_bindings
            ),
        )

        if trace.inference_id != expected_id:
            report.add_error(
                "Identifiant de trace "
                "non déterministe : "
                f"{trace.inference_id}"
            )

    @staticmethod
    def validate_trace_conclusion(
        report: InferenceValidationReport,
        trace: InferenceTrace,
        rule,
        premise_edges: list,
        inferred_edge: InferredEdge,
        inferred_edges_by_key: dict[
            EdgeKey,
            InferredEdge,
        ],
    ) -> None:
        try:
            if rule.rule_type == "inverse":
                conclusion, _, _ = (
                    apply_inverse_rule(
                        rule,
                        premise_edges[0],
                    )
                )
            elif rule.rule_type == "symmetry":
                conclusion, _, _ = (
                    apply_symmetry_rule(
                        rule,
                        premise_edges[0],
                    )
                )
            elif rule.rule_type == "transitivity":
                conclusion, _, _ = (
                    apply_transitivity_rule(
                        rule,
                        premise_edges[0],
                        premise_edges[1],
                    )
                )
            else:
                report.add_error(
                    "Type de règle inconnu : "
                    f"{trace.rule_id}"
                )
                return
        except (
            IndexError,
            ValueError,
        ) as error:
            report.add_error(
                "Conclusion impossible pour "
                "la trace : "
                f"{trace.inference_id} ({error})"
            )
            return

        inferred_key = canonical_edge_key(
            inferred_edge.subject_id,
            inferred_edge.predicate,
            inferred_edge.object_id,
        )

        if conclusion != inferred_key:
            report.add_error(
                "Conclusion incohérente : "
                f"{trace.inference_id}"
            )

        if inferred_key not in inferred_edges_by_key:
            report.add_error(
                "Conclusion absente des arêtes "
                "inférées : "
                f"{trace.inference_id}"
            )

    @staticmethod
    def compare_results(
        first: InferenceResult,
        second: InferenceResult,
    ) -> InferenceValidationReport:
        report = InferenceValidationReport()

        if first.to_dict() != second.to_dict():
            report.add_error(
                "Résultats d'inférence instables."
            )

        return report
