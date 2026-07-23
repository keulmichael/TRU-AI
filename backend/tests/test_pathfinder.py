from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.query.graph_index import GraphIndex
from tru_ai.query.pathfinder import (
    GraphPathfinder,
)


def make_pathfinder() -> GraphPathfinder:
    nodes = tuple(
        GraphNode(
            node_id=f"node-{letter}",
            label=letter.upper(),
            normalized_label=letter,
            node_type="entity",
        )
        for letter in ("a", "b", "c", "d")
    )

    edges = (
        GraphEdge(
            edge_id="edge-ab",
            subject_id="node-a",
            predicate="relie",
            object_id="node-b",
        ),
        GraphEdge(
            edge_id="edge-bc",
            subject_id="node-b",
            predicate="relie",
            object_id="node-c",
        ),
        GraphEdge(
            edge_id="edge-ad",
            subject_id="node-a",
            predicate="relie",
            object_id="node-d",
        ),
        GraphEdge(
            edge_id="edge-dc",
            subject_id="node-d",
            predicate="relie",
            object_id="node-c",
        ),
    )

    graph = KnowledgeGraph(
        nodes=nodes,
        edges=edges,
    )

    return GraphPathfinder(
        GraphIndex(graph)
    )


def test_shortest_path() -> None:
    pathfinder = make_pathfinder()

    path = pathfinder.shortest_path(
        source_id="node-a",
        target_id="node-c",
        directed=True,
    )

    assert path is not None
    assert path.length == 2
    assert path.node_ids[0] == "node-a"
    assert path.node_ids[-1] == "node-c"


def test_same_source_and_target() -> None:
    pathfinder = make_pathfinder()

    path = pathfinder.shortest_path(
        source_id="node-a",
        target_id="node-a",
    )

    assert path is not None
    assert path.length == 0
    assert path.node_ids == ("node-a",)


def test_returns_none_when_depth_too_low() -> None:
    pathfinder = make_pathfinder()

    path = pathfinder.shortest_path(
        source_id="node-a",
        target_id="node-c",
        directed=True,
        max_depth=1,
    )

    assert path is None


def test_undirected_path_can_reverse_edge() -> None:
    pathfinder = make_pathfinder()

    path = pathfinder.shortest_path(
        source_id="node-c",
        target_id="node-a",
        directed=False,
    )

    assert path is not None
    assert path.length == 2


def test_directed_path_cannot_reverse_edge() -> None:
    pathfinder = make_pathfinder()

    path = pathfinder.shortest_path(
        source_id="node-c",
        target_id="node-a",
        directed=True,
    )

    assert path is None