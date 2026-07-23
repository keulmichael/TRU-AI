from __future__ import annotations

from tru_ai.graph.models import GraphNode
from tru_ai.semantic.alias_registry import (
    SemanticAliasRegistry,
)
from tru_ai.semantic.candidate_generator import (
    SemanticCandidateGenerator,
)
from tru_ai.semantic.models import (
    MergeDecision,
    MergeEvidence,
    ResolutionResult,
)


class SemanticEntityResolver:
    def __init__(
        self,
        registry: SemanticAliasRegistry | None = None,
    ) -> None:
        self.registry = (
            registry or SemanticAliasRegistry()
        )

        self.candidate_generator = (
            SemanticCandidateGenerator(
                self.registry
            )
        )

    def resolve(
        self,
        nodes: tuple[GraphNode, ...],
    ) -> ResolutionResult:
        result = ResolutionResult(
            canonical_node_ids={
                node.node_id: node.node_id
                for node in nodes
            }
        )

        candidates = (
            self.candidate_generator.generate(
                nodes
            )
        )

        for first, second in candidates:
            decision = self.decide(
                first,
                second,
            )

            result.decisions.append(decision)

            if decision.decision == "merge":
                canonical = self.choose_canonical(
                    first,
                    second,
                )

                duplicate = (
                    second
                    if canonical.node_id
                    == first.node_id
                    else first
                )

                result.canonical_node_ids[
                    duplicate.node_id
                ] = canonical.node_id

            elif decision.decision == "review":
                result.unresolved_candidates.append(
                    decision
                )

        self.flatten_mapping(
            result.canonical_node_ids
        )

        return result

    def decide(
        self,
        first: GraphNode,
        second: GraphNode,
    ) -> MergeDecision:
        evidences: list[MergeEvidence] = []

        if (
            first.concept_id
            and second.concept_id
            and first.concept_id
            == second.concept_id
        ):
            evidences.append(
                MergeEvidence(
                    evidence_type="same_concept_id",
                    value=first.concept_id,
                    weight=1.0,
                )
            )

            return MergeDecision(
                source_node_id=second.node_id,
                target_node_id=first.node_id,
                decision="merge",
                confidence=1.0,
                rule_id="same_concept_id",
                evidences=tuple(evidences),
            )

        first_label = self.registry.resolve(
            first.normalized_label
            or first.label
        )

        second_label = self.registry.resolve(
            second.normalized_label
            or second.label
        )

        if first_label == second_label:
            evidences.append(
                MergeEvidence(
                    evidence_type=(
                        "same_canonical_label"
                    ),
                    value=first_label,
                    weight=0.98,
                )
            )

            return MergeDecision(
                source_node_id=second.node_id,
                target_node_id=first.node_id,
                decision="merge",
                confidence=0.98,
                rule_id="canonical_label_match",
                evidences=tuple(evidences),
            )

        first_aliases = {
            self.registry.resolve(alias)
            for alias in first.aliases
        }

        second_aliases = {
            self.registry.resolve(alias)
            for alias in second.aliases
        }

        if (
            first_label in second_aliases
            or second_label in first_aliases
            or first_aliases.intersection(
                second_aliases
            )
        ):
            evidences.append(
                MergeEvidence(
                    evidence_type="shared_alias",
                    value=(
                        first_label
                        if first_label
                        in second_aliases
                        else second_label
                    ),
                    weight=0.95,
                )
            )

            return MergeDecision(
                source_node_id=second.node_id,
                target_node_id=first.node_id,
                decision="merge",
                confidence=0.95,
                rule_id="shared_alias",
                evidences=tuple(evidences),
            )

        return MergeDecision(
            source_node_id=second.node_id,
            target_node_id=first.node_id,
            decision="keep_separate",
            confidence=1.0,
            rule_id="insufficient_equivalence",
            evidences=(),
        )

    @staticmethod
    def choose_canonical(
        first: GraphNode,
        second: GraphNode,
    ) -> GraphNode:
        def rank(
            node: GraphNode,
        ) -> tuple:
            return (
                0 if node.concept_id else 1,
                0
                if node.node_type == "concept"
                else 1,
                -node.occurrence_count,
                node.node_id,
            )

        return min(
            (first, second),
            key=rank,
        )

    @staticmethod
    def flatten_mapping(
        mapping: dict[str, str],
    ) -> None:
        for node_id in list(mapping):
            target_id = mapping[node_id]
            visited = {node_id}

            while (
                target_id in mapping
                and mapping[target_id]
                != target_id
            ):
                if target_id in visited:
                    raise RuntimeError(
                        "Cycle détecté dans "
                        "la résolution."
                    )

                visited.add(target_id)
                target_id = mapping[target_id]

            mapping[node_id] = target_id