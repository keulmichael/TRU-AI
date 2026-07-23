from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge
from tru_ai.inference.models import (
    EdgeKey,
    InferredEdge,
    canonical_edge_key,
)
from tru_ai.inference.rule import (
    apply_inverse_rule,
    apply_symmetry_rule,
    apply_transitivity_rule,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)


class PremiseEdge(Protocol):
    edge_id: str
    subject_id: str
    predicate: str
    object_id: str
    source_sentence_ids: set[str]
    confidence_max: float


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    premise_edges: tuple[PremiseEdge, ...]
    subject_id: str
    predicate: str
    object_id: str
    variable_bindings: dict[str, str]
    inference_depth: int
    confidence: float

    @property
    def edge_key(self) -> EdgeKey:
        return canonical_edge_key(
            self.subject_id,
            self.predicate,
            self.object_id,
        )

    @property
    def premise_edge_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                edge.edge_id
                for edge in self.premise_edges
            )
        )

    @property
    def premise_edge_keys(
        self,
    ) -> tuple[EdgeKey, ...]:
        return tuple(
            sorted(
                canonical_edge_key(
                    edge.subject_id,
                    edge.predicate,
                    edge.object_id,
                )
                for edge in self.premise_edges
            )
        )

    @property
    def source_sentence_ids(
        self,
    ) -> tuple[str, ...]:
        sentence_ids: set[str] = set()

        for edge in self.premise_edges:
            sentence_ids.update(
                edge.source_sentence_ids
            )

        return tuple(sorted(sentence_ids))


class InferenceMatcher:
    def __init__(
        self,
        graph: KnowledgeGraph,
        inferred_edges: tuple[InferredEdge, ...] = (),
    ) -> None:
        self.graph = graph
        self.inferred_edges = inferred_edges
        self.edges: tuple[
            PremiseEdge,
            ...
        ] = tuple(
            sorted(
                (
                    *graph.edges,
                    *inferred_edges,
                ),
                key=lambda edge: edge.edge_id,
            )
        )

        self.source_edge_keys = {
            canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            )
            for edge in graph.edges
        }

        self.existing_edge_keys = {
            canonical_edge_key(
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            )
            for edge in self.edges
        }

        self.edge_ids_by_predicate: dict[
            str,
            list[PremiseEdge],
        ] = defaultdict(list)

        self.edge_ids_by_subject: dict[
            str,
            list[PremiseEdge],
        ] = defaultdict(list)

        self.edge_ids_by_object: dict[
            str,
            list[PremiseEdge],
        ] = defaultdict(list)

        self.build_indexes()

    def build_indexes(self) -> None:
        for edge in self.edges:
            self.edge_ids_by_predicate[
                edge.predicate
            ].append(edge)
            self.edge_ids_by_subject[
                edge.subject_id
            ].append(edge)
            self.edge_ids_by_object[
                edge.object_id
            ].append(edge)

        for edge_ids in (
            self.edge_ids_by_predicate.values()
        ):
            edge_ids.sort(
                key=lambda edge: edge.edge_id
            )

        for edge_ids in (
            self.edge_ids_by_subject.values()
        ):
            edge_ids.sort(
                key=lambda edge: edge.edge_id
            )

        for edge_ids in (
            self.edge_ids_by_object.values()
        ):
            edge_ids.sort(
                key=lambda edge: edge.edge_id
            )

    def matches(
        self,
        registry: InferenceRuleRegistry,
        max_depth: int,
    ) -> tuple[RuleMatch, ...]:
        matches: list[RuleMatch] = []

        for rule in registry.active_rules():
            if rule.rule_type == "inverse":
                matches.extend(
                    self.match_unary_rule(
                        rule,
                        max_depth,
                        apply_inverse_rule,
                    )
                )
            elif rule.rule_type == "symmetry":
                matches.extend(
                    self.match_unary_rule(
                        rule,
                        max_depth,
                        apply_symmetry_rule,
                    )
                )
            elif rule.rule_type == "transitivity":
                matches.extend(
                    self.match_transitive_rule(
                        rule,
                        max_depth,
                    )
                )

        return tuple(
            sorted(
                matches,
                key=lambda match: (
                    match.inference_depth,
                    match.rule_id,
                    match.edge_key,
                    match.premise_edge_ids,
                ),
            )
        )

    def match_unary_rule(
        self,
        rule,
        max_depth: int,
        apply_rule,
    ) -> list[RuleMatch]:
        matches: list[RuleMatch] = []

        for edge in self.edge_ids_by_predicate.get(
            rule.source_predicate,
            [],
        ):
            conclusion, bindings, confidence = (
                apply_rule(rule, edge)
            )

            if not self.is_valid_conclusion(
                conclusion
            ):
                continue

            depth = (
                self.edge_depth(edge) + 1
            )

            if depth > max_depth:
                continue

            matches.append(
                RuleMatch(
                    rule_id=rule.rule_id,
                    premise_edges=(edge,),
                    subject_id=conclusion[0],
                    predicate=conclusion[1],
                    object_id=conclusion[2],
                    variable_bindings=bindings,
                    inference_depth=depth,
                    confidence=confidence,
                )
            )

        return matches

    def match_transitive_rule(
        self,
        rule,
        max_depth: int,
    ) -> list[RuleMatch]:
        matches: list[RuleMatch] = []

        first_edges = (
            self.edge_ids_by_predicate.get(
                rule.source_predicate,
                [],
            )
        )

        second_edges = first_edges

        for first_edge in first_edges:
            for second_edge in second_edges:
                if (
                    first_edge.edge_id
                    == second_edge.edge_id
                ):
                    continue

                if (
                    first_edge.object_id
                    != second_edge.subject_id
                ):
                    continue

                conclusion, bindings, confidence = (
                    apply_transitivity_rule(
                        rule,
                        first_edge,
                        second_edge,
                    )
                )

                if not self.is_valid_conclusion(
                    conclusion
                ):
                    continue

                depth = (
                    max(
                        self.edge_depth(
                            first_edge
                        ),
                        self.edge_depth(
                            second_edge
                        ),
                    )
                    + 1
                )

                if depth > max_depth:
                    continue

                matches.append(
                    RuleMatch(
                        rule_id=rule.rule_id,
                        premise_edges=(
                            first_edge,
                            second_edge,
                        ),
                        subject_id=conclusion[0],
                        predicate=conclusion[1],
                        object_id=conclusion[2],
                        variable_bindings=bindings,
                        inference_depth=depth,
                        confidence=confidence,
                    )
                )

        return matches

    def is_valid_conclusion(
        self,
        edge_key: EdgeKey,
    ) -> bool:
        subject_id, _, object_id = edge_key

        if subject_id == object_id:
            return False

        if edge_key in self.source_edge_keys:
            return False

        return True

    @staticmethod
    def edge_depth(
        edge: PremiseEdge,
    ) -> int:
        if isinstance(edge, InferredEdge):
            return edge.inference_depth

        return 0
