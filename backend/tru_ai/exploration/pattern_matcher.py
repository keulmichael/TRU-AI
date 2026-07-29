from __future__ import annotations

from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.models import (
    GraphPattern,
    PatternConstraint,
    PatternMatch,
    make_pattern_match_id,
)
from tru_ai.graph.models import GraphEdge


class ExplorationPatternMatcher:
    def __init__(
        self,
        indexes: ExplorationIndexes,
    ) -> None:
        self.indexes = indexes

    def match(
        self,
        pattern: GraphPattern,
    ) -> tuple[PatternMatch, ...]:
        self.validate(pattern)
        partials: list[tuple[dict[str, str], tuple[str, ...], float]] = [
            ({}, tuple(), 1.0)
        ]

        for constraint in pattern.constraints:
            next_partials: list[tuple[dict[str, str], tuple[str, ...], float]] = []
            candidate_edges = self.candidate_edges(
                constraint
            )
            for bindings, edge_ids, confidence in partials:
                for edge in candidate_edges:
                    updated = self.bind_constraint(
                        constraint,
                        edge.subject_id,
                        edge.object_id,
                        bindings,
                    )
                    if updated is None:
                        continue
                    next_partials.append(
                        (
                            updated,
                            (*edge_ids, edge.edge_id),
                            min(
                                confidence,
                                edge.confidence_average,
                            ),
                        )
                    )
            partials = self.deduplicate(next_partials)
            if not partials:
                break

        matches = []
        for bindings, edge_ids, confidence in partials:
            match_id = make_pattern_match_id(
                bindings,
                edge_ids,
            )
            matches.append(
                PatternMatch(
                    match_id=match_id,
                    bindings=dict(
                        sorted(bindings.items())
                    ),
                    edge_ids=tuple(sorted(edge_ids)),
                    confidence=round(confidence, 6),
                )
            )
        matches.sort(
            key=lambda match: match.match_id
        )
        return tuple(matches[: pattern.maximum_results])

    @staticmethod
    def validate(pattern: GraphPattern) -> None:
        if not 1 <= len(pattern.constraints) <= 4:
            raise ValueError(
                "Un motif doit contenir 1 à 4 contraintes."
            )
        if not 1 <= len(pattern.variables) <= 6:
            raise ValueError(
                "Un motif doit contenir 1 à 6 variables."
            )
        if not 1 <= pattern.maximum_results <= 500:
            raise ValueError(
                "maximum_results doit être entre 1 et 500."
            )

    def candidate_edges(
        self,
        constraint: PatternConstraint,
    ) -> tuple[GraphEdge, ...]:
        edges: tuple[GraphEdge, ...]
        if constraint.predicate is None:
            edges = self.indexes.graph.edges
        else:
            edge_ids = self.indexes.edge_ids_by_predicate.get(
                constraint.predicate,
                [],
            )
            edges = tuple(
                self.indexes.edges_by_id[edge_id]
                for edge_id in edge_ids
            )
        return tuple(
            sorted(
                edges,
                key=lambda edge: edge.edge_id,
            )
        )

    @staticmethod
    def bind_constraint(
        constraint: PatternConstraint,
        subject_id: str,
        object_id: str,
        bindings: dict[str, str],
    ) -> dict[str, str] | None:
        updated = dict(bindings)
        for token, value in (
            (constraint.subject, subject_id),
            (constraint.object, object_id),
        ):
            if token.startswith("?"):
                existing = updated.get(token)
                if existing and existing != value:
                    return None
                updated[token] = value
            elif token != value:
                return None
        return updated

    @staticmethod
    def deduplicate(partials):
        deduped = {}
        for bindings, edge_ids, confidence in partials:
            key = (
                tuple(sorted(bindings.items())),
                tuple(sorted(edge_ids)),
            )
            existing = deduped.get(key)
            if existing is None or confidence > existing[2]:
                deduped[key] = (
                    bindings,
                    tuple(sorted(edge_ids)),
                    confidence,
                )
        return [
            deduped[key]
            for key in sorted(deduped)
        ]
