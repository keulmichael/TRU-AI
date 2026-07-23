from tru_ai.inference.models import (
    InferenceResult,
    InferenceRule,
    InferenceTrace,
    InferenceValidationReport,
    InferredEdge,
    make_inference_id,
    make_inferred_edge_id,
)


def test_inferred_edge_id_is_stable() -> None:
    first = make_inferred_edge_id(
        "node-a",
        "is_a",
        "node-b",
    )

    second = make_inferred_edge_id(
        "node-a",
        "is_a",
        "node-b",
    )

    assert first == second
    assert first.startswith(
        "inferred-edge-"
    )


def test_inference_id_sorts_unordered_inputs() -> None:
    first = make_inference_id(
        rule_id="rule-1",
        premise_edge_ids=[
            "edge-b",
            "edge-a",
        ],
        premise_edge_keys=[
            (
                "b",
                "is_a",
                "c",
            ),
            (
                "a",
                "is_a",
                "b",
            ),
        ],
        subject_id="a",
        predicate="is_a",
        object_id="c",
        inference_depth=1,
        variable_bindings={
            "z": "c",
            "a": "a",
        },
    )

    second = make_inference_id(
        rule_id="rule-1",
        premise_edge_ids=[
            "edge-a",
            "edge-b",
        ],
        premise_edge_keys=[
            (
                "a",
                "is_a",
                "b",
            ),
            (
                "b",
                "is_a",
                "c",
            ),
        ],
        subject_id="a",
        predicate="is_a",
        object_id="c",
        inference_depth=1,
        variable_bindings={
            "a": "a",
            "z": "c",
        },
    )

    assert first == second
    assert first.startswith("inference-")


def test_inferred_edge_to_dict_is_deterministic() -> None:
    edge = InferredEdge(
        edge_id="inferred-edge-1",
        subject_id="node-a",
        predicate="is_a",
        object_id="node-c",
        rule_ids={
            "rule-b",
            "rule-a",
        },
        premise_edge_ids={
            "edge-b",
            "edge-a",
        },
        premise_edge_keys={
            (
                "node-b",
                "is_a",
                "node-c",
            ),
            (
                "node-a",
                "is_a",
                "node-b",
            ),
        },
        source_sentence_ids={
            "sentence-b",
            "sentence-a",
        },
        inference_depth=1,
        occurrence_count=2,
        confidence_sum=1.7,
        confidence_max=0.9,
    )

    record = edge.to_dict()

    assert record["rule_ids"] == [
        "rule-a",
        "rule-b",
    ]
    assert record["premise_edge_ids"] == [
        "edge-a",
        "edge-b",
    ]
    assert record["source_sentence_ids"] == [
        "sentence-a",
        "sentence-b",
    ]
    assert record["confidence_average"] == 0.85


def test_register_evidence_updates_confidence() -> None:
    edge = InferredEdge(
        edge_id="inferred-edge-1",
        subject_id="node-a",
        predicate="is_a",
        object_id="node-c",
    )

    edge.register_evidence(
        rule_id="rule-1",
        premise_edge_ids=["edge-1"],
        premise_edge_keys=[
            (
                "node-a",
                "is_a",
                "node-b",
            )
        ],
        source_sentence_ids=["sentence-1"],
        inference_depth=1,
        confidence=1.2,
    )

    assert edge.occurrence_count == 1
    assert edge.confidence_sum == 1.0
    assert edge.confidence_max == 1.0


def test_trace_to_dict_sorts_collections() -> None:
    trace = InferenceTrace(
        inference_id="inference-1",
        inferred_edge_id="inferred-edge-1",
        rule_id="rule-1",
        premise_edge_ids=(
            "edge-b",
            "edge-a",
        ),
        premise_edge_keys=(
            (
                "node-b",
                "is_a",
                "node-c",
            ),
            (
                "node-a",
                "is_a",
                "node-b",
            ),
        ),
        variable_bindings={
            "z": "node-c",
            "a": "node-a",
        },
        source_sentence_ids=(
            "sentence-b",
            "sentence-a",
        ),
        inference_depth=1,
        confidence=0.91234567,
    )

    record = trace.to_dict()

    assert record["premise_edge_ids"] == [
        "edge-a",
        "edge-b",
    ]
    assert list(
        record["variable_bindings"]
    ) == [
        "a",
        "z",
    ]
    assert record["confidence"] == 0.912346


def test_rule_and_result_to_dict() -> None:
    rule = InferenceRule(
        rule_id="rule-1",
        name="Rule",
        rule_type="inverse",
        rule_family="structural",
        source_predicate="contains",
        target_predicate="part_of",
        inverse_predicate="part_of",
        confidence_factor=1.0,
        enabled=True,
    )

    result = InferenceResult(
        inferred_edges=(),
        traces=(),
        passes_executed=1,
        max_depth_reached=0,
        fixed_point_reached=True,
    )

    assert rule.to_dict()["rule_id"] == "rule-1"
    assert result.to_dict() == {
        "inferred_edges": [],
        "traces": [],
        "passes_executed": 1,
        "max_depth_reached": 0,
        "fixed_point_reached": True,
    }


def test_validation_report_records_errors() -> None:
    report = InferenceValidationReport()

    report.add_warning("warning")
    report.add_error("error")

    assert report.valid is False
    assert report.to_dict() == {
        "valid": False,
        "errors": ["error"],
        "warnings": ["warning"],
    }
