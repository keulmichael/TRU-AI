from __future__ import annotations

from collections import Counter

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphValidationIssue,
    GraphValidationReport,
)


class KnowledgeGraphValidator:
    """Contrôle la cohérence structurelle du graphe."""

    def validate(
        self,
        graph: KnowledgeGraph,
    ) -> GraphValidationReport:
        issues: list[GraphValidationIssue] = []

        node_ids = {
            node.node_id
            for node in graph.nodes
        }

        connected_node_ids: set[str] = set()
        dangling_edge_count = 0
        self_loop_count = 0

        edge_signatures = []

        for edge in graph.edges:
            edge_signatures.append(
                (
                    edge.subject_id,
                    edge.predicate,
                    edge.object_id,
                )
            )

            subject_exists = (
                edge.subject_id in node_ids
            )

            object_exists = (
                edge.object_id in node_ids
            )

            if not subject_exists:
                dangling_edge_count += 1

                issues.append(
                    GraphValidationIssue(
                        issue_type=(
                            "missing_subject"
                        ),
                        severity="error",
                        message=(
                            "Le sujet de l'arête "
                            "n'existe pas dans les nœuds."
                        ),
                        resource_id=edge.edge_id,
                    )
                )

            if not object_exists:
                dangling_edge_count += 1

                issues.append(
                    GraphValidationIssue(
                        issue_type=(
                            "missing_object"
                        ),
                        severity="error",
                        message=(
                            "L'objet de l'arête "
                            "n'existe pas dans les nœuds."
                        ),
                        resource_id=edge.edge_id,
                    )
                )

            if subject_exists:
                connected_node_ids.add(
                    edge.subject_id
                )

            if object_exists:
                connected_node_ids.add(
                    edge.object_id
                )

            if (
                edge.subject_id
                == edge.object_id
            ):
                self_loop_count += 1

                issues.append(
                    GraphValidationIssue(
                        issue_type="self_loop",
                        severity="warning",
                        message=(
                            "Une relation relie un nœud "
                            "à lui-même."
                        ),
                        resource_id=edge.edge_id,
                    )
                )

        signature_counts = Counter(
            edge_signatures
        )

        duplicate_edge_count = sum(
            count - 1
            for count in signature_counts.values()
            if count > 1
        )

        if duplicate_edge_count:
            issues.append(
                GraphValidationIssue(
                    issue_type="duplicate_edges",
                    severity="error",
                    message=(
                        f"{duplicate_edge_count} arête(s) "
                        "dupliquée(s) détectée(s)."
                    ),
                )
            )

        isolated_node_ids = (
            node_ids - connected_node_ids
        )

        for node_id in sorted(
            isolated_node_ids
        ):
            issues.append(
                GraphValidationIssue(
                    issue_type="isolated_node",
                    severity="warning",
                    message=(
                        "Le nœud n'est relié à aucune "
                        "arête."
                    ),
                    resource_id=node_id,
                )
            )

        valid = not any(
            issue.severity == "error"
            for issue in issues
        )

        return GraphValidationReport(
            valid=valid,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            isolated_node_count=len(
                isolated_node_ids
            ),
            self_loop_count=self_loop_count,
            duplicate_edge_count=(
                duplicate_edge_count
            ),
            dangling_edge_count=(
                dangling_edge_count
            ),
            issues=tuple(issues),
        )