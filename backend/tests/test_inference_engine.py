from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.inference.engine import (
    InferenceEngine,
)


def make_node(
    node_id: str,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=node_id,
        normalized_label=node_id,
        node_type="concept",
        aliases={node_id},
        source_sentence_ids={
            f"sentence-{node_id}"
        },
        occurrence_count=1,
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


def result_keys(
    graph: KnowledgeGraph,
    max_depth: int = 2,
) -> set[tuple[str, str, str]]:
    result = InferenceEngine(
        max_depth=max_depth
    ).run(graph)

    return {
        (
            edge.subject_id,
            edge.predicate,
            edge.object_id,
        )
        for edge in result.inferred_edges
    }


def test_engine_applies_allowed_transitivity() -> None:
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

    assert result_keys(graph) == {
        (
            "node-a",
            "is_a",
            "node-c",
        )
    }


def test_engine_does_not_apply_observe_transitivity() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "observe",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "observe",
                "node-c",
            ),
        )
    )

    assert result_keys(graph) == set()


def test_engine_applies_inverse_rule() -> None:
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

    assert result_keys(graph) == {
        (
            "node-b",
            "part_of",
            "node-a",
        )
    }


def test_engine_applies_symmetry_rule() -> None:
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

    assert result_keys(graph) == {
        (
            "node-b",
            "equivalent_to",
            "node-a",
        )
    }


def test_engine_does_not_duplicate_existing_inverse() -> None:
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

    assert result_keys(graph) == set()


def test_engine_respects_depth_limit() -> None:
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
            make_edge(
                "edge-3",
                "node-c",
                "is_a",
                "node-d",
            ),
        )
    )

    assert result_keys(
        graph,
        max_depth=1,
    ) == {
        (
            "node-a",
            "is_a",
            "node-c",
        ),
        (
            "node-b",
            "is_a",
            "node-d",
        ),
    }

    assert (
        "node-a",
        "is_a",
        "node-d",
    ) in result_keys(
        graph,
        max_depth=2,
    )


def test_engine_reaches_fixed_point() -> None:
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

    result = InferenceEngine().run(graph)

    assert result.fixed_point_reached is True
    assert result.passes_executed == 2


def test_engine_preserves_provenance() -> None:
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

    result = InferenceEngine().run(graph)
    edge = result.inferred_edges[0]
    trace = result.traces[0]

    assert edge.rule_ids == {
        "transitivity-is_a"
    }
    assert edge.premise_edge_ids == {
        "edge-1",
        "edge-2",
    }
    assert edge.premise_edge_keys == {
        (
            "node-a",
            "is_a",
            "node-b",
        ),
        (
            "node-b",
            "is_a",
            "node-c",
        ),
    }
    assert edge.source_sentence_ids == {
        "sentence-edge-1",
        "sentence-edge-2",
    }
    assert trace.premise_edge_ids == (
        "edge-1",
        "edge-2",
    )


def test_engine_merges_multiple_proofs() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
                0.8,
            ),
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-d",
                0.8,
            ),
            make_edge(
                "edge-3",
                "node-a",
                "is_a",
                "node-c",
                0.7,
            ),
            make_edge(
                "edge-4",
                "node-c",
                "is_a",
                "node-d",
                0.7,
            ),
        )
    )

    result = InferenceEngine(
        max_depth=1
    ).run(graph)

    matching_edges = [
        edge
        for edge in result.inferred_edges
        if (
            edge.subject_id,
            edge.predicate,
            edge.object_id,
        )
        == (
            "node-a",
            "is_a",
            "node-d",
        )
    ]

    assert len(matching_edges) == 1
    assert matching_edges[0].occurrence_count == 2
    assert len(result.traces) == 2


def test_engine_is_deterministic() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-c",
            ),
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
        )
    )

    first = InferenceEngine().run(
        graph
    )
    second = InferenceEngine().run(
        graph
    )

    assert first.to_dict() == second.to_dict()
