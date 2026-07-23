from tru_ai.graph.builder import (
    KnowledgeGraph,
    KnowledgeGraphBuilder,
)
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.graph.validator import (
    KnowledgeGraphValidator,
)
from tru_ai.relations.models import Relation


def make_relation() -> Relation:
    return Relation(
        relation_id="relation-001",
        proposition_id="proposition-001",
        sentence_id="sentence-001",
        subject_id="legacy-subject",
        subject_label="conscience",
        predicate="observer",
        object_id="legacy-object",
        object_label="réalité",
        confidence=0.92,
        extraction_method=(
            "deterministic_pattern"
        ),
        pattern_id="transitive_verb",
    )


def test_valid_graph_passes_validation() -> None:
    builder = KnowledgeGraphBuilder()
    validator = KnowledgeGraphValidator()

    graph = builder.build(
        [make_relation()]
    )

    report = validator.validate(graph)

    assert report.valid is True
    assert report.dangling_edge_count == 0
    assert report.duplicate_edge_count == 0
    assert report.isolated_node_count == 0


def test_validator_detects_dangling_edge() -> None:
    validator = KnowledgeGraphValidator()

    node = GraphNode(
        node_id="node-a",
        label="A",
        normalized_label="a",
        node_type="entity",
    )

    edge = GraphEdge(
        edge_id="edge-001",
        subject_id="node-a",
        predicate="observer",
        object_id="node-missing",
    )

    graph = KnowledgeGraph(
        nodes=(node,),
        edges=(edge,),
    )

    report = validator.validate(graph)

    assert report.valid is False
    assert report.dangling_edge_count == 1


def test_validator_detects_isolated_node() -> None:
    validator = KnowledgeGraphValidator()

    node = GraphNode(
        node_id="node-a",
        label="A",
        normalized_label="a",
        node_type="entity",
    )

    graph = KnowledgeGraph(
        nodes=(node,),
        edges=(),
    )

    report = validator.validate(graph)

    assert report.valid is True
    assert report.isolated_node_count == 1


def test_validator_detects_self_loop() -> None:
    validator = KnowledgeGraphValidator()

    node = GraphNode(
        node_id="node-a",
        label="A",
        normalized_label="a",
        node_type="entity",
    )

    edge = GraphEdge(
        edge_id="edge-001",
        subject_id="node-a",
        predicate="etre",
        object_id="node-a",
    )

    graph = KnowledgeGraph(
        nodes=(node,),
        edges=(edge,),
    )

    report = validator.validate(graph)

    assert report.valid is True
    assert report.self_loop_count == 1