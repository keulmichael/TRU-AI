from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.semantic.graph_compactor import (
    SemanticGraphCompactor,
)
from tru_ai.semantic.models import ResolutionResult


def make_node(
    node_id: str,
    label: str,
    occurrence_count: int,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=label,
        normalized_label=label.lower(),
        node_type="concept",
        concept_id=None,
        category=None,
        aliases=set(),
        source_sentence_ids=set(),
        occurrence_count=occurrence_count,
    )


def make_edge(
    edge_id: str,
    subject_id: str,
    predicate: str,
    object_id: str,
    occurrence_count: int = 1,
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        relation_ids={f"relation-{edge_id}"},
        proposition_ids={f"proposition-{edge_id}"},
        source_sentence_ids={f"sentence-{edge_id}"},
        pattern_ids={"pattern-test"},
        extraction_methods={"deterministic"},
        occurrence_count=occurrence_count,
        confidence_sum=0.9 * occurrence_count,
        confidence_max=0.9,
    )


def test_compactor_preserves_occurrences():
    first = make_node(
        "node-1",
        "Conscience",
        2,
    )

    second = make_node(
        "node-2",
        "La conscience",
        3,
    )

    graph = KnowledgeGraph(
        nodes=(first, second),
        edges=(),
    )

    resolution = ResolutionResult(
        canonical_node_ids={
            "node-1": "node-1",
            "node-2": "node-1",
        }
    )

    compacted = SemanticGraphCompactor().compact(
        graph,
        resolution,
    )

    assert len(compacted.nodes) == 1
    assert compacted.nodes[0].occurrence_count == 5


def test_compactor_redirects_edges_to_canonical_node():
    duplicate = make_node(
        "node-1",
        "La conscience",
        1,
    )

    canonical = make_node(
        "node-2",
        "Conscience",
        1,
    )

    reality = make_node(
        "node-3",
        "Réalité",
        1,
    )

    edge = make_edge(
        "edge-1",
        "node-1",
        "observe",
        "node-3",
    )

    graph = KnowledgeGraph(
        nodes=(
            duplicate,
            canonical,
            reality,
        ),
        edges=(edge,),
    )

    resolution = ResolutionResult(
        canonical_node_ids={
            "node-1": "node-2",
            "node-2": "node-2",
            "node-3": "node-3",
        }
    )

    compacted = SemanticGraphCompactor().compact(
        graph,
        resolution,
    )

    assert compacted.edges[0].subject_id == "node-2"


def test_compactor_merges_duplicate_edges():
    duplicate = make_node(
        "node-1",
        "La conscience",
        1,
    )

    canonical = make_node(
        "node-2",
        "Conscience",
        1,
    )

    reality = make_node(
        "node-3",
        "Réalité",
        1,
    )

    first_edge = make_edge(
        "edge-1",
        "node-1",
        "observe",
        "node-3",
    )

    second_edge = make_edge(
        "edge-2",
        "node-2",
        "observe",
        "node-3",
    )

    graph = KnowledgeGraph(
        nodes=(
            duplicate,
            canonical,
            reality,
        ),
        edges=(
            first_edge,
            second_edge,
        ),
    )

    resolution = ResolutionResult(
        canonical_node_ids={
            "node-1": "node-2",
            "node-2": "node-2",
            "node-3": "node-3",
        }
    )

    compacted = SemanticGraphCompactor().compact(
        graph,
        resolution,
    )

    assert len(compacted.edges) == 1
    assert compacted.edges[0].occurrence_count == 2