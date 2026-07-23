from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.query.graph_index import GraphIndex


def make_graph() -> KnowledgeGraph:
    consciousness = GraphNode(
        node_id="concept-conscience",
        label="Conscience",
        normalized_label="conscience",
        node_type="concept",
        concept_id="conscience",
        aliases={
            "conscience",
            "la conscience",
        },
    )

    reality = GraphNode(
        node_id="concept-realite",
        label="Réalité",
        normalized_label="realite",
        node_type="concept",
        concept_id="realite",
        aliases={
            "réalité",
            "realite",
        },
    )

    edge = GraphEdge(
        edge_id="edge-001",
        subject_id=(
            consciousness.node_id
        ),
        predicate="observer",
        object_id=reality.node_id,
        occurrence_count=1,
        confidence_sum=0.92,
        confidence_max=0.92,
    )

    return KnowledgeGraph(
        nodes=(
            consciousness,
            reality,
        ),
        edges=(edge,),
    )


def test_index_finds_node_by_label() -> None:
    index = GraphIndex(make_graph())

    assert index.find_exact_node_ids(
        "Conscience"
    ) == ("concept-conscience",)


def test_index_finds_node_by_alias() -> None:
    index = GraphIndex(make_graph())

    assert index.find_exact_node_ids(
        "la conscience"
    ) == ("concept-conscience",)


def test_index_returns_outgoing_edges() -> None:
    index = GraphIndex(make_graph())

    edges = index.get_outgoing_edges(
        "concept-conscience"
    )

    assert len(edges) == 1
    assert edges[0].predicate == "observer"


def test_index_returns_incoming_edges() -> None:
    index = GraphIndex(make_graph())

    edges = index.get_incoming_edges(
        "concept-realite"
    )

    assert len(edges) == 1
    assert edges[0].predicate == "observer"


def test_index_finds_predicate() -> None:
    index = GraphIndex(make_graph())

    edges = index.get_edges_by_predicate(
        "observer"
    )

    assert len(edges) == 1