from dataclasses import replace

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.inference.engine import InferenceEngine
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.reasoning.explainer import (
    ReasoningExplainer,
)
from tru_ai.reasoning.models import (
    ReasoningResult,
)
from tru_ai.reasoning.proof_builder import (
    ProofBuilder,
)
from tru_ai.reasoning.validator import (
    ReasoningValidator,
)


def make_graph():
    nodes = (
        GraphNode(
            "node-a",
            "A",
            "a",
            "concept",
        ),
        GraphNode(
            "node-b",
            "B",
            "b",
            "concept",
        ),
    )
    edges = (
        GraphEdge(
            "edge-1",
            "node-a",
            "contains",
            "node-b",
            source_sentence_ids={"sentence-1"},
            occurrence_count=1,
            confidence_sum=0.9,
            confidence_max=0.9,
        ),
    )
    return KnowledgeGraph(nodes, edges)


def make_valid_context():
    graph = make_graph()
    inference = InferenceEngine().run(graph)
    enriched = (
        InferenceRepository.build_enriched_graph(
            graph,
            inference.inferred_edges,
        )
    )
    proof_trees, _ = ProofBuilder(
        enriched,
        inference.inferred_edges,
        inference.traces,
    ).build_all()
    explanations = ReasoningExplainer(
        enriched,
        inference.inferred_edges,
        inference.traces,
    ).explain_all(proof_trees)
    result = ReasoningResult(
        explanations=explanations,
        proof_trees=proof_trees,
        explained_edge_count=len(
            explanations
        ),
        unexplained_edge_ids=(),
    )
    return graph, inference, enriched, result


def validate(enriched, inference, result):
    return ReasoningValidator().validate(
        enriched,
        inference.inferred_edges,
        inference.traces,
        result,
    )


def test_validator_accepts_valid_result() -> None:
    _, inference, enriched, result = (
        make_valid_context()
    )

    assert validate(
        enriched,
        inference,
        result,
    ).valid is True


def test_validator_detects_unexplained_edge() -> None:
    _, inference, enriched, result = (
        make_valid_context()
    )
    broken = ReasoningResult(
        explanations=(),
        proof_trees=(),
        explained_edge_count=0,
        unexplained_edge_ids=(),
    )

    assert validate(
        enriched,
        inference,
        broken,
    ).valid is False


def test_validator_detects_missing_tree() -> None:
    _, inference, enriched, result = (
        make_valid_context()
    )
    explanation = replace(
        result.explanations[0],
        proof_tree_id="missing-tree",
    )
    broken = ReasoningResult(
        explanations=(explanation,),
        proof_trees=result.proof_trees,
        explained_edge_count=1,
        unexplained_edge_ids=(),
    )

    assert validate(
        enriched,
        inference,
        broken,
    ).valid is False


def test_validator_detects_bad_step_order() -> None:
    _, inference, enriched, result = (
        make_valid_context()
    )
    steps = tuple(reversed(result.explanations[0].steps))
    explanation = replace(
        result.explanations[0],
        steps=steps,
    )
    broken = ReasoningResult(
        explanations=(explanation,),
        proof_trees=result.proof_trees,
        explained_edge_count=1,
        unexplained_edge_ids=(),
    )

    assert validate(
        enriched,
        inference,
        broken,
    ).valid is False


def test_validator_detects_bad_text() -> None:
    _, inference, enriched, result = (
        make_valid_context()
    )
    explanation = replace(
        result.explanations[0],
        deterministic_text="bad",
    )
    broken = ReasoningResult(
        explanations=(explanation,),
        proof_trees=result.proof_trees,
        explained_edge_count=1,
        unexplained_edge_ids=(),
    )

    assert validate(
        enriched,
        inference,
        broken,
    ).valid is False


def test_validator_detects_cycle() -> None:
    _, inference, enriched, result = (
        make_valid_context()
    )
    tree = result.proof_trees[0]
    cyclic = replace(
        tree,
        children=(tree,),
    )
    broken = ReasoningResult(
        explanations=result.explanations,
        proof_trees=(cyclic,),
        explained_edge_count=1,
        unexplained_edge_ids=(),
    )

    assert validate(
        enriched,
        inference,
        broken,
    ).valid is False


def test_validator_compare_results_detects_instability() -> None:
    _, _, _, result = make_valid_context()
    broken = ReasoningResult(
        explanations=(),
        proof_trees=result.proof_trees,
        explained_edge_count=0,
        unexplained_edge_ids=(),
    )

    assert (
        ReasoningValidator.compare_results(
            result,
            broken,
        ).valid
        is False
    )
