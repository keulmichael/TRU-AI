from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
    ReasoningResult,
    ReasoningStep,
    ReasoningValidationReport,
    make_explanation_id,
    make_proof_node_id,
    make_reasoning_step_id,
)


def test_reasoning_ids_are_stable() -> None:
    edge_key = (
        "node-a",
        "is_a",
        "node-b",
    )

    assert make_reasoning_step_id(
        "edge-1",
        "premise",
        0,
    ) == make_reasoning_step_id(
        "edge-1",
        "premise",
        0,
    )

    assert make_proof_node_id(
        "edge-1",
        edge_key,
        "source_fact",
        None,
        0,
        (),
    ).startswith("proof-node-")

    assert make_proof_node_id(
        "edge-1",
        edge_key,
        "inferred_fact",
        "rule-b",
        1,
        ("child-b", "child-a"),
        root=True,
    ) == make_proof_node_id(
        "edge-1",
        edge_key,
        "inferred_fact",
        "rule-b",
        1,
        ("child-a", "child-b"),
        root=True,
    )

    assert make_explanation_id(
        "edge-1",
        edge_key,
        "proof-tree-1",
        ("rule-b", "rule-a"),
    ) == make_explanation_id(
        "edge-1",
        edge_key,
        "proof-tree-1",
        ("rule-a", "rule-b"),
    )


def test_reasoning_step_to_dict_is_stable() -> None:
    step = ReasoningStep(
        step_id="step-1",
        step_number=1,
        edge_id="edge-1",
        edge_key=(
            "node-a",
            "is_a",
            "node-b",
        ),
        role="premise",
        depth=0,
        confidence=0.91234567,
        source_sentence_ids=(
            "sentence-b",
            "sentence-a",
        ),
    )

    assert step.to_dict() == {
        "step_id": "step-1",
        "step_number": 1,
        "edge_id": "edge-1",
        "edge_key": [
            "node-a",
            "is_a",
            "node-b",
        ],
        "role": "premise",
        "depth": 0,
        "confidence": 0.912346,
        "source_sentence_ids": [
            "sentence-a",
            "sentence-b",
        ],
    }


def test_proof_tree_to_dict_is_recursive() -> None:
    child = ProofTreeNode(
        node_id="proof-node-child",
        edge_id="edge-1",
        edge_key=(
            "node-a",
            "is_a",
            "node-b",
        ),
        node_type="source_fact",
        rule_id=None,
        confidence=0.9,
        depth=0,
    )

    root = ProofTreeNode(
        node_id="proof-tree-root",
        edge_id="edge-2",
        edge_key=(
            "node-a",
            "is_a",
            "node-c",
        ),
        node_type="inferred_fact",
        rule_id="transitivity-is_a",
        confidence=0.8,
        depth=1,
        children=(child,),
    )

    assert root.to_dict()["children"][0][
        "node_id"
    ] == "proof-node-child"


def test_explanation_and_result_to_dict() -> None:
    step = ReasoningStep(
        step_id="step-1",
        step_number=1,
        edge_id="edge-1",
        edge_key=("a", "p", "b"),
        role="conclusion",
        depth=1,
        confidence=0.8,
        source_sentence_ids=(),
    )

    explanation = ReasoningExplanation(
        explanation_id="explanation-1",
        inferred_edge_id="edge-1",
        conclusion_edge_key=("a", "p", "b"),
        rule_ids=("rule-b", "rule-a"),
        steps=(step,),
        proof_tree_id="proof-tree-1",
        maximum_depth=1,
        confidence=0.8,
        deterministic_text="text",
    )

    result = ReasoningResult(
        explanations=(explanation,),
        proof_trees=(),
        explained_edge_count=1,
        unexplained_edge_ids=(
            "edge-b",
            "edge-a",
        ),
    )

    assert explanation.to_dict()["rule_ids"] == [
        "rule-a",
        "rule-b",
    ]
    assert result.to_dict()[
        "unexplained_edge_ids"
    ] == [
        "edge-a",
        "edge-b",
    ]


def test_reasoning_validation_report() -> None:
    report = ReasoningValidationReport()
    report.add_warning("warning")
    report.add_error("error")

    assert report.to_dict() == {
        "valid": False,
        "errors": ["error"],
        "warnings": ["warning"],
    }
