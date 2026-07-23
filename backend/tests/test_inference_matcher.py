from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.inference.matcher import (
    InferenceMatcher,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)


def make_node(
    node_id: str,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=node_id,
        normalized_label=node_id,
        node_type="concept",
    )


def make_edge(
    edge_id: str,
    subject_id: str,
    predicate: str,
    object_id: str,
    confidence: float = 0.9,
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        source_sentence_ids={
            f"sentence-{edge_id}"
        },
        occurrence_count=1,
        confidence_sum=confidence,
        confidence_max=confidence,
    )


def make_graph(
    edges: tuple[GraphEdge, ...],
) -> KnowledgeGraph:
    node_ids = sorted(
        {
            node_id
            for edge in edges
            for node_id in (
                edge.subject_id,
                edge.object_id,
            )
        }
    )

    return KnowledgeGraph(
        nodes=tuple(
            make_node(node_id)
            for node_id in node_ids
        ),
        edges=edges,
    )


def match_keys(
    graph: KnowledgeGraph,
) -> list[tuple[str, str, str]]:
    matcher = InferenceMatcher(graph)

    return [
        match.edge_key
        for match in matcher.matches(
            InferenceRuleRegistry.default(),
            max_depth=2,
        )
    ]


def test_matcher_matches_inverse_rule() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            ),
        )
    )

    assert (
        "node-b",
        "part_of",
        "node-a",
    ) in match_keys(graph)


def test_matcher_matches_symmetry_rule() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "equivalent_to",
                "node-b",
            ),
        )
    )

    assert (
        "node-b",
        "equivalent_to",
        "node-a",
    ) in match_keys(graph)


def test_matcher_matches_transitive_rule() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-c",
            ),
        )
    )

    assert (
        "node-a",
        "is_a",
        "node-c",
    ) in match_keys(graph)


def test_matcher_requires_transitive_unification() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-d",
                "is_a",
                "node-c",
            ),
        )
    )

    assert (
        "node-a",
        "is_a",
        "node-c",
    ) not in match_keys(graph)


def test_matcher_excludes_self_loops() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-a",
            ),
        )
    )

    assert (
        "node-a",
        "is_a",
        "node-a",
    ) not in match_keys(graph)


def test_matcher_excludes_existing_source_triplets() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "part_of",
                "node-a",
            ),
        )
    )

    assert (
        "node-b",
        "part_of",
        "node-a",
    ) not in match_keys(graph)


def test_matcher_order_is_stable() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-2",
                "node-b",
                "contains",
                "node-c",
            ),
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            ),
        )
    )

    first = match_keys(graph)
    second = match_keys(graph)

    assert first == second
