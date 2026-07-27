from tests.test_exploration_indexes import make_graph
from tru_ai.exploration.engine import ExplorationEngine
from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.models import GraphQuery


def make_engine() -> ExplorationEngine:
    return ExplorationEngine(
        ExplorationIndexes(make_graph())
    )


def test_get_neighbors_outgoing() -> None:
    neighbors = make_engine().get_neighbors(
        "node-a",
        direction="outgoing",
    )

    assert neighbors == (("edge-1", "node-b"),)


def test_get_neighbors_incoming() -> None:
    neighbors = make_engine().get_neighbors(
        "node-a",
        direction="incoming",
    )

    assert neighbors == (
        ("inferred-edge-1", "node-b"),
    )


def test_filters_by_predicate_and_confidence() -> None:
    engine = make_engine()

    assert engine.get_neighbors(
        "node-a",
        predicates=("missing",),
    ) == ()
    assert engine.get_neighbors(
        "node-a",
        minimum_confidence=0.95,
    ) == ()


def test_excludes_source_or_inferred_edges() -> None:
    engine = make_engine()

    assert engine.get_neighbors(
        "node-a",
        direction="outgoing",
        include_source_edges=False,
    ) == ()
    assert engine.get_neighbors(
        "node-a",
        direction="incoming",
        include_inferred_edges=False,
    ) == ()


def test_neighborhood_depth_one() -> None:
    result = make_engine().get_neighborhood(
        "node-a",
        maximum_depth=1,
    )

    assert result.node_ids == (
        "node-a",
        "node-b",
    )
    assert "edge-1" in result.edge_ids


def test_neighborhood_prevents_cycles() -> None:
    result = make_engine().get_neighborhood(
        "node-a",
        maximum_depth=3,
    )

    assert result.node_ids == (
        "node-a",
        "node-b",
    )


def test_execute_query_returns_exploration_result() -> None:
    result = make_engine().execute_query(
        GraphQuery(
            start_node_id="node-a",
            maximum_depth=1,
        )
    )

    assert result.nodes
    assert result.edges
