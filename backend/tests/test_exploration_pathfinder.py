from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.pathfinder import ExplorationPathfinder
from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.reasoning.models import ReasoningExplanation


def node(node_id: str) -> GraphNode:
    return GraphNode(node_id, node_id, node_id, "concept")


def edge(edge_id, s, p, o, confidence=0.9, inferred=False):
    return GraphEdge(
        edge_id=edge_id,
        subject_id=s,
        predicate=p,
        object_id=o,
        extraction_methods=(
            {"deterministic_inference"}
            if inferred
            else set()
        ),
        occurrence_count=1,
        confidence_sum=confidence,
        confidence_max=confidence,
    )


def make_pathfinder():
    graph = KnowledgeGraph(
        nodes=tuple(node(n) for n in ("a", "b", "c", "d")),
        edges=(
            edge("e1", "a", "p", "b", 0.9),
            edge("e2", "b", "p", "c", 0.8, True),
            edge("e3", "a", "q", "c", 0.7),
            edge("e4", "c", "p", "d", 0.9),
        ),
    )
    explanation = ReasoningExplanation(
        explanation_id="explanation-e2",
        inferred_edge_id="e2",
        conclusion_edge_key=("b", "p", "c"),
        rule_ids=("rule",),
        steps=(),
        proof_tree_id="tree",
        maximum_depth=1,
        confidence=0.8,
        deterministic_text="text",
    )
    return ExplorationPathfinder(
        ExplorationIndexes(graph, (explanation,))
    )


def test_direct_path() -> None:
    paths = make_pathfinder().find_paths("a", "c", limit=10)

    assert paths[0].length == 1
    assert paths[0].steps[0].edge_id == "e3"


def test_multi_hop_path_and_explanation() -> None:
    paths = make_pathfinder().find_paths(
        "a",
        "c",
        predicates=("p",),
        limit=10,
    )

    assert paths[0].length == 2
    assert paths[0].steps[1].explanation_id == "explanation-e2"


def test_no_path() -> None:
    assert make_pathfinder().find_paths("d", "a") == ()


def test_path_ranking_is_deterministic() -> None:
    first = [
        path.to_dict()
        for path in make_pathfinder().find_paths("a", "c", limit=10)
    ]
    second = [
        path.to_dict()
        for path in make_pathfinder().find_paths("a", "c", limit=10)
    ]

    assert first == second


def test_simple_paths_do_not_repeat_nodes() -> None:
    for path in make_pathfinder().find_paths("a", "d", maximum_depth=3):
        nodes = [path.start_node_id]
        for step in path.steps:
            nodes.append(step.object_id)
        assert len(nodes) == len(set(nodes))
