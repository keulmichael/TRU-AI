from tru_ai.graph.models import GraphNode
from tru_ai.semantic.resolver import (
    SemanticEntityResolver,
)


def make_node(
    node_id: str,
    label: str,
    normalized_label: str,
    concept_id: str | None = None,
    occurrence_count: int = 1,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=label,
        normalized_label=normalized_label,
        node_type="concept",
        concept_id=concept_id,
        category=None,
        aliases=set(),
        source_sentence_ids=set(),
        occurrence_count=occurrence_count,
    )


def test_resolver_merges_same_concept_id():
    resolver = SemanticEntityResolver()

    first = make_node(
        node_id="node-1",
        label="Conscience",
        normalized_label="conscience",
        concept_id="concept-conscience",
    )

    second = make_node(
        node_id="node-2",
        label="La conscience",
        normalized_label="la conscience",
        concept_id="concept-conscience",
    )

    result = resolver.resolve(
        (first, second)
    )

    assert (
        result.canonical_id("node-1")
        == result.canonical_id("node-2")
    )

    assert any(
        decision.decision == "merge"
        for decision in result.decisions
    )


def test_resolver_merges_alias_variants():
    resolver = SemanticEntityResolver()

    first = make_node(
        node_id="node-1",
        label="Conscience",
        normalized_label="conscience",
    )

    second = make_node(
        node_id="node-2",
        label="La conscience",
        normalized_label="la conscience",
    )

    result = resolver.resolve(
        (first, second)
    )

    assert (
        result.canonical_id("node-1")
        == result.canonical_id("node-2")
    )


def test_resolver_does_not_merge_related_concepts():
    resolver = SemanticEntityResolver()

    consciousness = make_node(
        node_id="node-1",
        label="Conscience",
        normalized_label="conscience",
    )

    universal_consciousness = make_node(
        node_id="node-2",
        label="Conscience universelle",
        normalized_label="conscience universelle",
    )

    result = resolver.resolve(
        (
            consciousness,
            universal_consciousness,
        )
    )

    assert (
        result.canonical_id("node-1")
        != result.canonical_id("node-2")
    )