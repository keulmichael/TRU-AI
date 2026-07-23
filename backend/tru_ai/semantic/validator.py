from __future__ import annotations

from dataclasses import dataclass, field

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.semantic.models import (
    ResolutionResult,
)


@dataclass
class SemanticValidationReport:
    valid: bool = True
    errors: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def add_error(
        self,
        message: str,
    ) -> None:
        self.valid = False
        self.errors.append(message)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class SemanticGraphValidator:
    def validate(
        self,
        original_graph: KnowledgeGraph,
        resolved_graph: KnowledgeGraph,
        resolution: ResolutionResult,
    ) -> SemanticValidationReport:
        report = SemanticValidationReport()

        original_node_ids = {
            node.node_id
            for node in original_graph.nodes
        }

        resolved_node_ids = {
            node.node_id
            for node in resolved_graph.nodes
        }

        for source_id in original_node_ids:
            target_id = resolution.canonical_id(
                source_id
            )

            if target_id not in resolved_node_ids:
                report.add_error(
                    "Cible canonique absente : "
                    f"{source_id} → {target_id}"
                )

        for edge in resolved_graph.edges:
            if edge.subject_id not in resolved_node_ids:
                report.add_error(
                    "Sujet absent pour l'arête "
                    f"{edge.edge_id}."
                )

            if edge.object_id not in resolved_node_ids:
                report.add_error(
                    "Objet absent pour l'arête "
                    f"{edge.edge_id}."
                )

        original_occurrences = sum(
            node.occurrence_count
            for node in original_graph.nodes
        )

        resolved_occurrences = sum(
            node.occurrence_count
            for node in resolved_graph.nodes
        )

        if (
            original_occurrences
            != resolved_occurrences
        ):
            report.add_error(
                "Le nombre total d'occurrences "
                "des nœuds n'est pas conservé."
            )

        return report