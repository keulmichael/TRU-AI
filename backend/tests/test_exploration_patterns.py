from tests.test_exploration_pathfinder import edge, node
from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.models import (
    GraphPattern,
    PatternConstraint,
)
from tru_ai.exploration.pattern_matcher import (
    ExplorationPatternMatcher,
)
from tru_ai.graph.builder import KnowledgeGraph


def make_matcher():
    graph = KnowledgeGraph(
        nodes=tuple(node(n) for n in ("a", "b", "c")),
        edges=(
            edge("e1", "a", "is_a", "b", 0.9),
            edge("e2", "b", "part_of", "c", 0.8),
            edge("e3", "a", "related_to", "c", 0.7),
        ),
    )
    return ExplorationPatternMatcher(
        ExplorationIndexes(graph)
    )


def test_single_constraint_pattern() -> None:
    matches = make_matcher().match(
        GraphPattern(
            variables=("?x", "?y"),
            constraints=(
                PatternConstraint("?x", "is_a", "?y"),
            ),
        )
    )

    assert matches[0].bindings == {"?x": "a", "?y": "b"}


def test_two_constraint_pattern_joins_bindings() -> None:
    matches = make_matcher().match(
        GraphPattern(
            variables=("?x", "?y", "?z"),
            constraints=(
                PatternConstraint("?x", "is_a", "?y"),
                PatternConstraint("?y", "part_of", "?z"),
            ),
        )
    )

    assert matches[0].bindings["?z"] == "c"
    assert matches[0].confidence == 0.8


def test_constant_binding() -> None:
    matches = make_matcher().match(
        GraphPattern(
            variables=("?x",),
            constraints=(
                PatternConstraint("?x", None, "c"),
            ),
        )
    )

    assert {
        match.bindings["?x"]
        for match in matches
    } == {"a", "b"}


def test_pattern_deduplicates_and_is_stable() -> None:
    pattern = GraphPattern(
        variables=("?x", "?y"),
        constraints=(
            PatternConstraint("?x", "is_a", "?y"),
        ),
    )

    assert [
        match.to_dict()
        for match in make_matcher().match(pattern)
    ] == [
        match.to_dict()
        for match in make_matcher().match(pattern)
    ]


def test_pattern_limits_are_validated() -> None:
    try:
        make_matcher().match(
            GraphPattern(
                variables=("?x",),
                constraints=(),
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid pattern accepted")
