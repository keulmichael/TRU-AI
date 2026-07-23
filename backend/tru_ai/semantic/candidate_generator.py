from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from tru_ai.graph.models import GraphNode
from tru_ai.semantic.alias_registry import (
    SemanticAliasRegistry,
)


class SemanticCandidateGenerator:
    def __init__(
        self,
        registry: SemanticAliasRegistry | None = None,
    ) -> None:
        self.registry = (
            registry or SemanticAliasRegistry()
        )

    def generate(
        self,
        nodes: tuple[GraphNode, ...],
    ) -> list[tuple[GraphNode, GraphNode]]:
        groups: dict[
            str,
            list[GraphNode],
        ] = defaultdict(list)

        for node in nodes:
            canonical_label = (
                self.registry.resolve(
                    node.normalized_label
                    or node.label
                )
            )

            groups[canonical_label].append(node)

            if node.concept_id:
                concept_key = (
                    f"concept:{node.concept_id}"
                )
                groups[concept_key].append(node)

            for alias in node.aliases:
                alias_key = (
                    self.registry.resolve(alias)
                )
                groups[alias_key].append(node)

        candidate_ids: set[
            tuple[str, str]
        ] = set()

        nodes_by_id = {
            node.node_id: node
            for node in nodes
        }

        for group in groups.values():
            unique_group = {
                node.node_id: node
                for node in group
            }

            for first, second in combinations(
                sorted(
                    unique_group.values(),
                    key=lambda item: item.node_id,
                ),
                2,
            ):
                pair = tuple(
                    sorted(
                        (
                            first.node_id,
                            second.node_id,
                        )
                    )
                )

                candidate_ids.add(pair)

        return [
            (
                nodes_by_id[first_id],
                nodes_by_id[second_id],
            )
            for first_id, second_id
            in sorted(candidate_ids)
        ]