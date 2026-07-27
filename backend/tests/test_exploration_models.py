from tru_ai.exploration.models import (
    GraphPath,
    GraphPathStep,
    GraphPattern,
    GraphQuery,
    PatternConstraint,
    PatternMatch,
    make_path_id,
    make_pattern_match_id,
)


def test_path_id_is_deterministic() -> None:
    assert make_path_id(
        "a",
        "c",
        ("e1", "e2"),
    ) == make_path_id(
        "a",
        "c",
        ("e1", "e2"),
    )


def test_pattern_match_id_sorts_inputs() -> None:
    assert make_pattern_match_id(
        {"?b": "b", "?a": "a"},
        ("e2", "e1"),
    ) == make_pattern_match_id(
        {"?a": "a", "?b": "b"},
        ("e1", "e2"),
    )


def test_graph_query_to_dict_sorts_predicates() -> None:
    query = GraphQuery(
        predicates=("z", "a"),
        minimum_confidence=0.1234567,
    )

    assert query.to_dict()["predicates"] == [
        "a",
        "z",
    ]
    assert query.to_dict()["minimum_confidence"] == 0.123457


def test_graph_path_to_dict() -> None:
    step = GraphPathStep(
        position=1,
        edge_id="edge-1",
        subject_id="a",
        predicate="is_a",
        object_id="b",
        direction="outgoing",
        inferred=True,
        confidence=0.91234567,
        explanation_id="explanation-1",
    )
    path = GraphPath(
        path_id="path-1",
        start_node_id="a",
        end_node_id="b",
        steps=(step,),
        length=1,
        minimum_confidence=0.91234567,
        inferred_edge_count=1,
    )

    record = path.to_dict()

    assert record["steps"][0]["confidence"] == 0.912346
    assert record["minimum_confidence"] == 0.912346


def test_pattern_models_to_dict() -> None:
    pattern = GraphPattern(
        variables=("?z", "?a"),
        constraints=(
            PatternConstraint(
                subject="?a",
                predicate=None,
                object="?z",
            ),
        ),
        maximum_results=10,
    )
    match = PatternMatch(
        match_id="match-1",
        bindings={"?z": "z", "?a": "a"},
        edge_ids=("e2", "e1"),
        confidence=0.8,
    )

    assert pattern.to_dict()["variables"] == [
        "?a",
        "?z",
    ]
    assert match.to_dict()["edge_ids"] == [
        "e1",
        "e2",
    ]
