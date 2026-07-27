from __future__ import annotations

from dataclasses import dataclass, field

from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.models import (
    GraphPath,
    PatternMatch,
)


@dataclass
class ExplorationValidationReport:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ExplorationValidator:
    def validate_indexes(
        self,
        indexes: ExplorationIndexes,
    ) -> ExplorationValidationReport:
        report = ExplorationValidationReport()
        node_ids = set(indexes.nodes_by_id)
        edge_ids = set(indexes.edges_by_id)

        for edge in indexes.graph.edges:
            if edge.subject_id not in node_ids:
                report.add_error(
                    f"Sujet absent : {edge.edge_id}"
                )
            if edge.object_id not in node_ids:
                report.add_error(
                    f"Objet absent : {edge.edge_id}"
                )

        for node_id, ids in indexes.outgoing_edge_ids.items():
            if ids != sorted(set(ids)):
                report.add_error(
                    f"Index sortant non stable : {node_id}"
                )
            for edge_id in ids:
                edge = indexes.edges_by_id.get(edge_id)
                if edge is None or edge.subject_id != node_id:
                    report.add_error(
                        f"Index sortant incohérent : {edge_id}"
                    )

        for node_id, ids in indexes.incoming_edge_ids.items():
            if ids != sorted(set(ids)):
                report.add_error(
                    f"Index entrant non stable : {node_id}"
                )
            for edge_id in ids:
                edge = indexes.edges_by_id.get(edge_id)
                if edge is None or edge.object_id != node_id:
                    report.add_error(
                        f"Index entrant incohérent : {edge_id}"
                    )

        for predicate, ids in indexes.edge_ids_by_predicate.items():
            if ids != sorted(set(ids)):
                report.add_error(
                    f"Index prédicat non stable : {predicate}"
                )
            for edge_id in ids:
                edge = indexes.edges_by_id.get(edge_id)
                if edge is None or edge.predicate != predicate:
                    report.add_error(
                        f"Index prédicat incohérent : {edge_id}"
                    )

        for edge_id in indexes.explanations_by_edge_id:
            if edge_id not in edge_ids:
                report.add_error(
                    f"Explication sans arête : {edge_id}"
                )

        return report

    @staticmethod
    def validate_paths(
        paths: tuple[GraphPath, ...],
    ) -> ExplorationValidationReport:
        report = ExplorationValidationReport()
        for path in paths:
            if path.length != len(path.steps):
                report.add_error(
                    f"Longueur incohérente : {path.path_id}"
                )
            nodes = [path.start_node_id]
            for step in path.steps:
                nodes.append(step.object_id)
            if len(nodes) != len(set(nodes)):
                report.add_error(
                    f"Nœud répété : {path.path_id}"
                )
        return report

    @staticmethod
    def compare_results(first, second) -> ExplorationValidationReport:
        report = ExplorationValidationReport()
        if first.to_dict() != second.to_dict():
            report.add_error("Résultat instable.")
        return report

    @staticmethod
    def validate_pattern_matches(
        matches: tuple[PatternMatch, ...],
    ) -> ExplorationValidationReport:
        report = ExplorationValidationReport()
        seen = set()
        for match in matches:
            key = (
                tuple(sorted(match.bindings.items())),
                tuple(sorted(match.edge_ids)),
            )
            if key in seen:
                report.add_error(
                    f"Motif dupliqué : {match.match_id}"
                )
            seen.add(key)
        return report
