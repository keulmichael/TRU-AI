from dataclasses import replace

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.inference.engine import (
    InferenceEngine,
)
from tru_ai.inference.models import (
    InferenceResult,
    InferenceTrace,
    InferredEdge,
    make_inference_id,
    make_inferred_edge_id,
)
from tru_ai.inference.validator import (
    InferenceValidator,
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


def make_graph() -> KnowledgeGraph:
    return KnowledgeGraph(
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


def make_valid_result():
    graph = make_graph()
    result = InferenceEngine(
        max_depth=1
    ).run(graph)

    return graph, result


def validate(
    graph,
    result,
    max_depth: int = 1,
):
    return InferenceValidator(
        max_depth=max_depth
    ).validate(graph, result)


def replace_edge(
    result: InferenceResult,
    edge: InferredEdge,
) -> InferenceResult:
    return InferenceResult(
        inferred_edges=(edge,),
        traces=result.traces,
        passes_executed=result.passes_executed,
        max_depth_reached=(
            result.max_depth_reached
        ),
        fixed_point_reached=(
            result.fixed_point_reached
        ),
    )


def replace_trace(
    result: InferenceResult,
    trace: InferenceTrace,
) -> InferenceResult:
    return InferenceResult(
        inferred_edges=result.inferred_edges,
        traces=(trace,),
        passes_executed=result.passes_executed,
        max_depth_reached=(
            result.max_depth_reached
        ),
        fixed_point_reached=(
            result.fixed_point_reached
        ),
    )


def test_validator_accepts_valid_result() -> None:
    graph, result = make_valid_result()

    report = validate(graph, result)

    assert report.valid is True
    assert report.errors == []


def test_validator_detects_missing_node() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    broken = replace_edge(
        result,
        InferredEdge(
            edge_id=make_inferred_edge_id(
                "missing-node",
                edge.predicate,
                edge.object_id,
            ),
            subject_id="missing-node",
            predicate=edge.predicate,
            object_id=edge.object_id,
            rule_ids=set(edge.rule_ids),
            premise_edge_ids=set(
                edge.premise_edge_ids
            ),
            premise_edge_keys=set(
                edge.premise_edge_keys
            ),
            source_sentence_ids=set(
                edge.source_sentence_ids
            ),
            inference_depth=1,
            occurrence_count=1,
            confidence_sum=edge.confidence_sum,
            confidence_max=edge.confidence_max,
        ),
    )

    assert validate(graph, broken).valid is False


def test_validator_detects_missing_rule() -> None:
    graph, result = make_valid_result()
    trace = replace(
        result.traces[0],
        rule_id="missing-rule",
    )

    report = validate(
        graph,
        replace_trace(result, trace),
    )

    assert report.valid is False
    assert any(
        "Règle absente" in error
        for error in report.errors
    )


def test_validator_detects_missing_premise() -> None:
    graph, result = make_valid_result()
    trace = replace(
        result.traces[0],
        premise_edge_ids=("missing-edge",),
    )

    report = validate(
        graph,
        replace_trace(result, trace),
    )

    assert report.valid is False
    assert any(
        "Prémisse absente" in error
        for error in report.errors
    )


def test_validator_detects_incoherent_premise_key() -> None:
    graph, result = make_valid_result()
    trace = replace(
        result.traces[0],
        premise_edge_keys=(
            (
                "node-x",
                "is_a",
                "node-y",
            ),
        ),
    )

    report = validate(
        graph,
        replace_trace(result, trace),
    )

    assert report.valid is False
    assert any(
        "Clé de prémisse incohérente"
        in error
        for error in report.errors
    )


def test_validator_detects_source_duplicate() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    duplicate = InferredEdge(
        edge_id=make_inferred_edge_id(
            "node-a",
            "is_a",
            "node-b",
        ),
        subject_id="node-a",
        predicate="is_a",
        object_id="node-b",
        rule_ids=set(edge.rule_ids),
        premise_edge_ids=set(edge.premise_edge_ids),
        premise_edge_keys=set(edge.premise_edge_keys),
        source_sentence_ids=set(
            edge.source_sentence_ids
        ),
        inference_depth=1,
        occurrence_count=1,
        confidence_sum=0.8,
        confidence_max=0.8,
    )

    report = validate(
        graph,
        replace_edge(result, duplicate),
    )

    assert report.valid is False
    assert any(
        "déjà présente" in error
        for error in report.errors
    )


def test_validator_detects_duplicate_inferred_edge() -> None:
    graph, result = make_valid_result()

    broken = InferenceResult(
        inferred_edges=(
            result.inferred_edges[0],
            result.inferred_edges[0],
        ),
        traces=result.traces,
        passes_executed=1,
        max_depth_reached=1,
        fixed_point_reached=True,
    )

    report = validate(graph, broken)

    assert report.valid is False
    assert any(
        "dupliquée" in error
        for error in report.errors
    )


def test_validator_detects_depth_too_high() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    edge.inference_depth = 2

    report = validate(graph, result, max_depth=1)

    assert report.valid is False
    assert any(
        "supérieure" in error
        for error in report.errors
    )


def test_validator_detects_zero_depth() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    edge.inference_depth = 0

    report = validate(graph, result)

    assert report.valid is False
    assert any(
        "Profondeur inférée invalide"
        in error
        for error in report.errors
    )


def test_validator_detects_invalid_confidence() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    edge.confidence_max = 1.5
    edge.confidence_sum = 1.5

    report = validate(graph, result)

    assert report.valid is False
    assert any(
        "Confiance maximale invalide"
        in error
        for error in report.errors
    )


def test_validator_detects_confidence_sum_error() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    edge.confidence_sum = 0.1
    edge.confidence_max = 0.5

    report = validate(graph, result)

    assert report.valid is False
    assert any(
        "Somme de confiance incohérente"
        in error
        for error in report.errors
    )


def test_validator_detects_invalid_occurrence_count() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    edge.occurrence_count = 0

    report = validate(graph, result)

    assert report.valid is False
    assert any(
        "occurrences invalide" in error
        for error in report.errors
    )


def test_validator_detects_invalid_edge_id() -> None:
    graph, result = make_valid_result()
    edge = result.inferred_edges[0]
    edge.edge_id = "bad-id"

    report = validate(graph, result)

    assert report.valid is False
    assert any(
        "Identifiant d'arête" in error
        for error in report.errors
    )


def test_validator_detects_invalid_trace_id() -> None:
    graph, result = make_valid_result()
    trace = replace(
        result.traces[0],
        inference_id="bad-id",
    )

    report = validate(
        graph,
        replace_trace(result, trace),
    )

    assert report.valid is False
    assert any(
        "Identifiant de trace" in error
        for error in report.errors
    )


def test_validator_detects_self_loop() -> None:
    graph, result = make_valid_result()
    edge = InferredEdge(
        edge_id=make_inferred_edge_id(
            "node-a",
            "is_a",
            "node-a",
        ),
        subject_id="node-a",
        predicate="is_a",
        object_id="node-a",
        inference_depth=1,
        occurrence_count=1,
        confidence_sum=0.8,
        confidence_max=0.8,
    )

    report = validate(
        graph,
        replace_edge(result, edge),
    )

    assert report.valid is False
    assert any(
        "Self-loop" in error
        for error in report.errors
    )


def test_validator_detects_unstable_result() -> None:
    graph, result = make_valid_result()
    trace = result.traces[0]
    unstable_trace = replace(
        trace,
        inference_id=make_inference_id(
            rule_id=trace.rule_id,
            premise_edge_ids=trace.premise_edge_ids,
            premise_edge_keys=trace.premise_edge_keys,
            subject_id=(
                result.inferred_edges[0].subject_id
            ),
            predicate=(
                result.inferred_edges[0].predicate
            ),
            object_id=(
                result.inferred_edges[0].object_id
            ),
            inference_depth=(
                trace.inference_depth
            ),
            variable_bindings={
                **trace.variable_bindings,
                "extra": "unstable",
            },
        ),
        variable_bindings={
            **trace.variable_bindings,
            "extra": "unstable",
        },
    )

    broken = replace_trace(
        result,
        unstable_trace,
    )

    report = (
        InferenceValidator.compare_results(
            result,
            broken,
        )
    )

    assert report.valid is False
    assert any(
        "instables" in error
        for error in report.errors
    )
