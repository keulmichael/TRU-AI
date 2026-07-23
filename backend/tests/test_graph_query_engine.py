from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.query.engine import (
    GraphQueryEngine,
)
from tru_ai.query.graph_index import GraphIndex


def make_engine() -> GraphQueryEngine:
    nodes = (
        GraphNode(
            node_id="concept-conscience",
            label="Conscience",
            normalized_label="conscience",
            node_type="concept",
            concept_id="conscience",
            aliases={"conscience"},
        ),
        GraphNode(
            node_id="concept-realite",
            label="Réalité",
            normalized_label="realite",
            node_type="concept",
            concept_id="realite",
            aliases={"réalité"},
        ),
        GraphNode(
            node_id="concept-reconnaissance",
            label="Reconnaissance",
            normalized_label="reconnaissance",
            node_type="concept",
            concept_id="reconnaissance",
            aliases={"reconnaissance"},
        ),
    )

    edges = (
        GraphEdge(
            edge_id="edge-001",
            subject_id="concept-conscience",
            predicate="observer",
            object_id="concept-realite",
            occurrence_count=1,
            confidence_sum=0.92,
            confidence_max=0.92,
        ),
        GraphEdge(
            edge_id="edge-002",
            subject_id=(
                "concept-reconnaissance"
            ),
            predicate="transformer",
            object_id="concept-conscience",
            occurrence_count=1,
            confidence_sum=0.90,
            confidence_max=0.90,
        ),
    )

    graph = KnowledgeGraph(
        nodes=nodes,
        edges=edges,
    )

    return GraphQueryEngine(
        GraphIndex(graph)
    )


def test_find_node() -> None:
    engine = make_engine()

    node = engine.find_node(
        "conscience"
    )

    assert node is not None
    assert (
        node.node_id
        == "concept-conscience"
    )


def test_search_nodes() -> None:
    engine = make_engine()

    results = engine.search_nodes(
        "recon"
    )

    assert len(results) == 1
    assert (
        results[0].node_id
        == "concept-reconnaissance"
    )


def test_outgoing_relations() -> None:
    engine = make_engine()

    relations = engine.outgoing(
        "conscience"
    )

    assert len(relations) == 1
    assert (
        relations[0].object_label
        == "Réalité"
    )


def test_incoming_relations() -> None:
    engine = make_engine()

    relations = engine.incoming(
        "conscience"
    )

    assert len(relations) == 1
    assert (
        relations[0].subject_label
        == "Reconnaissance"
    )


def test_neighbors_both_directions() -> None:
    engine = make_engine()

    neighbors = engine.neighbors(
        "conscience",
        direction="both",
    )

    assert len(neighbors) == 2

    labels = {
        neighbor.label
        for neighbor in neighbors
    }

    assert labels == {
        "Réalité",
        "Reconnaissance",
    }


def test_find_by_predicate() -> None:
    engine = make_engine()

    relations = (
        engine.find_by_predicate(
            "transformer"
        )
    )

    assert len(relations) == 1
    assert (
        relations[0].object_label
        == "Conscience"
    )