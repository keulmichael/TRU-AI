from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.inference.engine import InferenceEngine
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.reasoning.explainer import (
    ReasoningExplainer,
)
from tru_ai.reasoning.proof_builder import (
    ProofBuilder,
)


def make_node(node_id: str) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=node_id.upper(),
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


def make_explanation():
    graph = KnowledgeGraph(
        nodes=(
            make_node("node-a"),
            make_node("node-b"),
            make_node("node-c"),
        ),
        edges=(
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
        ),
    )
    inference = InferenceEngine(
        max_depth=1
    ).run(graph)
    enriched = (
        InferenceRepository.build_enriched_graph(
            graph,
            inference.inferred_edges,
        )
    )
    tree = ProofBuilder(
        enriched,
        inference.inferred_edges,
        inference.traces,
    ).build_for_edge(
        inference.inferred_edges[0].edge_id
    )

    return ReasoningExplainer(
        enriched,
        inference.inferred_edges,
        inference.traces,
    ).explain(tree)


def test_explainer_orders_steps_sources_before_conclusion() -> None:
    explanation = make_explanation()

    assert [
        step.role
        for step in explanation.steps
    ] == [
        "premise",
        "premise",
        "conclusion",
    ]
    assert [
        step.step_number
        for step in explanation.steps
    ] == [1, 2, 3]


def test_explainer_builds_deterministic_text() -> None:
    explanation = make_explanation()

    assert explanation.deterministic_text == (
        "Conclusion:\n"
        "NODE-A is_a NODE-C\n"
        "\n"
        "Rule:\n"
        "Transitivity of is_a\n"
        "\n"
        "Premises:\n"
        "1. NODE-A is_a NODE-B\n"
        "2. NODE-B is_a NODE-C\n"
        "\n"
        "Depth:\n"
        "1\n"
        "\n"
        "Confidence:\n"
        "0.855000"
    )


def test_explainer_is_deterministic() -> None:
    first = make_explanation()
    second = make_explanation()

    assert first.to_dict() == second.to_dict()
