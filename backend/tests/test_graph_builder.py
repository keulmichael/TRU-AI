from tru_ai.graph.builder import (
    KnowledgeGraphBuilder,
)
from tru_ai.relations.models import Relation


def make_relation(
    relation_id: str = "relation-001",
    proposition_id: str = "proposition-001",
    sentence_id: str = "sentence-001",
    subject_label: str = "conscience",
    predicate: str = "observer",
    object_label: str = "réalité",
    confidence: float = 0.92,
) -> Relation:
    return Relation(
        relation_id=relation_id,
        proposition_id=proposition_id,
        sentence_id=sentence_id,
        subject_id="legacy-subject",
        subject_label=subject_label,
        predicate=predicate,
        object_id="legacy-object",
        object_label=object_label,
        confidence=confidence,
        extraction_method=(
            "deterministic_pattern"
        ),
        pattern_id="transitive_verb",
    )


def test_builder_creates_nodes_and_edge() -> None:
    builder = KnowledgeGraphBuilder()

    graph = builder.build(
        [make_relation()]
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

    edge = graph.edges[0]

    assert edge.subject_id == (
        "concept-conscience"
    )

    assert edge.object_id == (
        "concept-realite"
    )

    assert edge.predicate == "observer"


def test_builder_deduplicates_nodes() -> None:
    builder = KnowledgeGraphBuilder()

    relations = [
        make_relation(
            relation_id="relation-001",
            sentence_id="sentence-001",
        ),
        make_relation(
            relation_id="relation-002",
            proposition_id="proposition-002",
            sentence_id="sentence-002",
            predicate="transformer",
        ),
    ]

    graph = builder.build(relations)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 2


def test_builder_merges_identical_edges() -> None:
    builder = KnowledgeGraphBuilder()

    relations = [
        make_relation(
            relation_id="relation-001",
            sentence_id="sentence-001",
            confidence=0.90,
        ),
        make_relation(
            relation_id="relation-002",
            proposition_id="proposition-002",
            sentence_id="sentence-002",
            confidence=0.80,
        ),
    ]

    graph = builder.build(relations)

    assert len(graph.edges) == 1

    edge = graph.edges[0]

    assert edge.occurrence_count == 2
    import pytest
    assert edge.confidence_max == 0.90


def test_builder_preserves_sources() -> None:
    builder = KnowledgeGraphBuilder()

    relations = [
        make_relation(
            relation_id="relation-001",
            sentence_id="sentence-001",
        ),
        make_relation(
            relation_id="relation-002",
            proposition_id="proposition-002",
            sentence_id="sentence-002",
        ),
    ]

    graph = builder.build(relations)

    edge = graph.edges[0]

    assert edge.source_sentence_ids == {
        "sentence-001",
        "sentence-002",
    }


def test_adjacency_contains_both_directions() -> None:
    builder = KnowledgeGraphBuilder()

    graph = builder.build(
        [make_relation()]
    )

    adjacency = graph.build_adjacency()

    subject_adjacency = adjacency[
        "concept-conscience"
    ]

    object_adjacency = adjacency[
        "concept-realite"
    ]

    assert len(
        subject_adjacency["outgoing"]
    ) == 1

    assert len(
        object_adjacency["incoming"]
    ) == 1