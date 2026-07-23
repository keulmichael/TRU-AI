from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphNode
from tru_ai.semantic.models import ResolutionResult
from tru_ai.semantic.validator import (
    SemanticGraphValidator,
)


def make_node(
    node_id: str,
    occurrence_count: int = 1,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=node_id,
        normalized_label=node_id,
        node_type="concept",
        concept_id=None,
        category=None,
        aliases=set(),
        source_sentence_ids=set(),
        occurrence_count=occurrence_count,
    )


def test_semantic_graph_is_valid():
    original = KnowledgeGraph(
        nodes=(
            make_node("node-1", 1),
            make_node("node-2", 2),
        ),
        edges=(),
    )

    resolved = KnowledgeGraph(
        nodes=(
            make_node("node-1", 3),
        ),
        edges=(),
    )

    resolution = ResolutionResult(
        canonical_node_ids={
            "node-1": "node-1",
            "node-2": "node-1",
        }
    )

    report = SemanticGraphValidator().validate(
        original_graph=original,
        resolved_graph=resolved,
        resolution=resolution,
    )

    assert report.valid is True
    assert report.errors == []


def test_validator_detects_occurrence_loss():
    original = KnowledgeGraph(
        nodes=(
            make_node("node-1", 2),
        ),
        edges=(),
    )

    resolved = KnowledgeGraph(
        nodes=(
            make_node("node-1", 1),
        ),
        edges=(),
    )

    resolution = ResolutionResult(
        canonical_node_ids={
            "node-1": "node-1",
        }
    )

    report = SemanticGraphValidator().validate(
        original_graph=original,
        resolved_graph=resolved,
        resolution=resolution,
    )

    assert report.valid is False
    assert report.errors