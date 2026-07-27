from tests.test_exploration_indexes import make_graph
from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.pathfinder import ExplorationPathfinder
from tru_ai.exploration.validator import ExplorationValidator
from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode


def test_validator_accepts_valid_indexes() -> None:
    report = ExplorationValidator().validate_indexes(
        ExplorationIndexes(make_graph())
    )

    assert report.valid is True


def test_validator_detects_missing_node_reference() -> None:
    graph = KnowledgeGraph(
        nodes=(GraphNode("a", "A", "a", "concept"),),
        edges=(
            GraphEdge(
                "e",
                "a",
                "p",
                "missing",
                occurrence_count=1,
                confidence_sum=1.0,
                confidence_max=1.0,
            ),
        ),
    )
    report = ExplorationValidator().validate_indexes(
        ExplorationIndexes(graph)
    )

    assert report.valid is False


def test_validator_validates_paths() -> None:
    indexes = ExplorationIndexes(make_graph())
    paths = ExplorationPathfinder(indexes).find_paths(
        "node-a",
        "node-b",
    )

    assert ExplorationValidator.validate_paths(paths).valid is True


def test_validator_detects_unstable_result() -> None:
    indexes = ExplorationIndexes(make_graph())
    first = indexes.search_nodes(None, 10)
    second = tuple(reversed(first))

    class Result:
        def __init__(self, value):
            self.value = value

        def to_dict(self):
            return {"value": self.value}

    assert (
        ExplorationValidator.compare_results(
            Result(first),
            Result(second),
        ).valid
        is False
    )
