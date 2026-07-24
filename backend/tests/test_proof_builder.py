from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.inference.engine import InferenceEngine
from tru_ai.inference.models import (
    InferenceResult,
    InferenceTrace,
)
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.reasoning.proof_builder import (
    ProofBuilder,
)


def make_node(node_id: str) -> GraphNode:
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
        confidence_sum=0.9,
        confidence_max=0.9,
    )


def make_graph(edges) -> KnowledgeGraph:
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
        edges=tuple(edges),
    )


def build_reasoning_graph(graph):
    result = InferenceEngine().run(graph)
    enriched = (
        InferenceRepository.build_enriched_graph(
            graph,
            result.inferred_edges,
        )
    )
    return result, enriched


def test_builder_builds_inverse_proof() -> None:
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            )
        ]
    )
    result, enriched = build_reasoning_graph(graph)

    tree = ProofBuilder(
        enriched,
        result.inferred_edges,
        result.traces,
    ).build_for_edge(
        result.inferred_edges[0].edge_id
    )

    assert tree.node_type == "inferred_fact"
    assert tree.rule_id == "inverse-contains-to-part_of"
    assert len(tree.children) == 1
    assert tree.children[0].node_type == "source_fact"


def test_builder_builds_symmetry_proof() -> None:
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "equivalent_to",
                "node-b",
            )
        ]
    )
    result, enriched = build_reasoning_graph(graph)
    tree = ProofBuilder(
        enriched,
        result.inferred_edges,
        result.traces,
    ).build_for_edge(
        result.inferred_edges[0].edge_id
    )

    assert tree.rule_id == "symmetry-equivalent_to"
    assert tree.children[0].edge_key == (
        "node-a",
        "equivalent_to",
        "node-b",
    )


def test_builder_builds_transitive_proof() -> None:
    graph = make_graph(
        [
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
        ]
    )
    result, enriched = build_reasoning_graph(graph)
    tree = ProofBuilder(
        enriched,
        result.inferred_edges,
        result.traces,
    ).build_for_edge(
        result.inferred_edges[0].edge_id
    )

    assert tree.depth == 1
    assert len(tree.children) == 2


def test_builder_builds_recursive_depth_two_proof() -> None:
    graph = make_graph(
        [
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
        ]
    )
    result, enriched = build_reasoning_graph(graph)
    target = [
        edge
        for edge in result.inferred_edges
        if edge.object_id == "node-d"
        and edge.subject_id == "node-a"
    ][0]
    tree = ProofBuilder(
        enriched,
        result.inferred_edges,
        result.traces,
    ).build_for_edge(target.edge_id)

    assert tree.depth == 2
    assert any(
        child.node_type == "inferred_fact"
        for child in tree.children
    )


def test_builder_selects_trace_deterministically() -> None:
    graph = make_graph(
        [
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
                "node-d",
            ),
            make_edge(
                "edge-3",
                "node-a",
                "is_a",
                "node-c",
            ),
            make_edge(
                "edge-4",
                "node-c",
                "is_a",
                "node-d",
            ),
        ]
    )
    result, enriched = build_reasoning_graph(graph)
    target = result.inferred_edges[0]
    builder = ProofBuilder(
        enriched,
        result.inferred_edges,
        tuple(reversed(result.traces)),
    )

    assert builder.select_trace(
        target.edge_id
    ) == builder.select_trace(
        target.edge_id
    )


def test_builder_detects_cycle() -> None:
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            )
        ]
    )
    result, enriched = build_reasoning_graph(graph)
    trace = result.traces[0]
    cyclic_trace = InferenceTrace(
        inference_id=trace.inference_id,
        inferred_edge_id=trace.inferred_edge_id,
        rule_id=trace.rule_id,
        premise_edge_ids=(
            trace.inferred_edge_id,
        ),
        premise_edge_keys=(
            trace.premise_edge_keys[0],
        ),
        variable_bindings=trace.variable_bindings,
        source_sentence_ids=trace.source_sentence_ids,
        inference_depth=trace.inference_depth,
        confidence=trace.confidence,
    )

    builder = ProofBuilder(
        enriched,
        result.inferred_edges,
        (cyclic_trace,),
    )

    try:
        builder.build_for_edge(
            trace.inferred_edge_id
        )
    except ValueError as error:
        assert "Cycle" in str(error)
    else:
        raise AssertionError("cycle not detected")


def test_builder_reports_missing_premise() -> None:
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            )
        ]
    )
    result, enriched = build_reasoning_graph(graph)
    trace = result.traces[0]
    broken_trace = InferenceTrace(
        inference_id=trace.inference_id,
        inferred_edge_id=trace.inferred_edge_id,
        rule_id=trace.rule_id,
        premise_edge_ids=("missing-edge",),
        premise_edge_keys=trace.premise_edge_keys,
        variable_bindings=trace.variable_bindings,
        source_sentence_ids=trace.source_sentence_ids,
        inference_depth=trace.inference_depth,
        confidence=trace.confidence,
    )
    proof_trees, unexplained = ProofBuilder(
        enriched,
        result.inferred_edges,
        (broken_trace,),
    ).build_all()

    assert proof_trees == ()
    assert unexplained == (
        trace.inferred_edge_id,
    )
