from __future__ import annotations

import pytest

from tru_ai.cognitive.reasoning import (
    ReasoningPlanner,
    ReasoningRequest,
    ReasoningStage,
    TruthStatus,
)


def test_default_plan_contains_full_reflexive_sequence() -> None:
    planner = ReasoningPlanner()

    plan = planner.plan(
        ReasoningRequest(
            question="  Analyse le concept de reconnaissance.  ",
            intent="concept_explanation",
        )
    )

    assert plan.question == "Analyse le concept de reconnaissance."
    assert plan.intent == "concept_explanation"
    assert plan.policy_version == "tru-reasoning-v1"

    assert tuple(step.stage for step in plan.steps) == (
        ReasoningStage.OBSERVATION,
        ReasoningStage.CONTEXT,
        ReasoningStage.EXPLICIT_CLAIMS,
        ReasoningStage.DEDUCTIONS,
        ReasoningStage.HYPOTHESES,
        ReasoningStage.RECOGNITION,
        ReasoningStage.DELTA,
        ReasoningStage.REFLEXIVITY,
        ReasoningStage.RECOGNITION_MEANING,
        ReasoningStage.THEORY_CONSTRUCTION,
        ReasoningStage.THEORY_COMPARISON,
        ReasoningStage.THEORY_EVOLUTION,
        ReasoningStage.PREDICTION,
        ReasoningStage.SCIENTIFIC_GAPS,
        ReasoningStage.CONTRADICTIONS,
        ReasoningStage.MISSING_KNOWLEDGE,
        ReasoningStage.SYNTHESIS,
    )

    assert tuple(step.position for step in plan.steps) == tuple(range(1, 18))


def test_supporting_arguments_plan_is_reduced() -> None:
    planner = ReasoningPlanner()

    plan = planner.plan(
        ReasoningRequest(
            question="Quels sont les arguments ?",
            intent="supporting_arguments",
        )
    )

    assert tuple(step.stage for step in plan.steps) == (
        ReasoningStage.OBSERVATION,
        ReasoningStage.CONTEXT,
        ReasoningStage.EXPLICIT_CLAIMS,
        ReasoningStage.DEDUCTIONS,
        ReasoningStage.SYNTHESIS,
    )


def test_contradiction_review_includes_contradiction_stage() -> None:
    planner = ReasoningPlanner()

    plan = planner.plan(
        ReasoningRequest(
            question="Quelles contradictions vois-tu ?",
            intent="contradiction_review",
        )
    )

    assert ReasoningStage.CONTRADICTIONS in {
        step.stage
        for step in plan.steps
    }


def test_reflexivity_review_contains_reflexivity_stage() -> None:
    planner = ReasoningPlanner()
    plan = planner.plan(
        ReasoningRequest(
            question="Quelles boucles réflexives sont présentes ?",
            intent="reflexivity_review",
        )
    )
    assert tuple(step.stage for step in plan.steps) == (
        ReasoningStage.OBSERVATION,
        ReasoningStage.CONTEXT,
        ReasoningStage.EXPLICIT_CLAIMS,
        ReasoningStage.RECOGNITION,
        ReasoningStage.DELTA,
        ReasoningStage.REFLEXIVITY,
        ReasoningStage.RECOGNITION_MEANING,
        ReasoningStage.SYNTHESIS,
    )


def test_reflexivity_step_declares_inputs_and_outputs() -> None:
    planner = ReasoningPlanner()
    plan = planner.plan(
        ReasoningRequest(
            question="Analyse la réflexivité.",
            intent="reflexivity_review",
        )
    )
    step = next(
        step for step in plan.steps
        if step.stage is ReasoningStage.REFLEXIVITY
    )
    assert step.inputs == (
        "recognition_graph",
        "recognition_patterns",
        "delta_comparisons",
    )
    assert step.outputs == (
        "reflexive_graph",
        "reflexive_relations",
        "reflexive_loops",
    )


def test_empty_question_is_rejected() -> None:
    planner = ReasoningPlanner()

    with pytest.raises(
        ValueError,
        match="La question ne peut pas être vide",
    ):
        planner.plan(
            ReasoningRequest(
                question="   ",
                intent="concept_explanation",
            )
        )


def test_empty_intent_is_rejected() -> None:
    planner = ReasoningPlanner()

    with pytest.raises(
        ValueError,
        match="L'intention ne peut pas être vide",
    ):
        planner.plan(
            ReasoningRequest(
                question="Explique le Delta.",
                intent=" ",
            )
        )


def test_truth_status_values_preserve_tru_vocabulary() -> None:
    assert TruthStatus.EXPLICIT.value == "EXPLICITE"
    assert TruthStatus.DEDUCTION.value == "DÉDUCTION"
    assert TruthStatus.HYPOTHESIS.value == "HYPOTHÈSE"
    assert TruthStatus.UNKNOWN.value == "INCONNU"


def test_plan_is_json_serializable() -> None:
    planner = ReasoningPlanner()

    payload = planner.plan(
        ReasoningRequest(
            question="Explique le Delta.",
            intent="concept_explanation",
        )
    ).to_dict()

    assert payload["steps"][0]["stage"] == "observation"
    assert payload["steps"][-1]["stage"] == "synthesis"
    assert isinstance(payload["steps"][0]["inputs"], list)
    assert isinstance(payload["steps"][0]["outputs"], list)


def test_recognition_meaning_step_declares_inputs_and_outputs() -> None:
    planner = ReasoningPlanner()
    plan = planner.plan(
        ReasoningRequest(
            question="Que reconnaît le système ?",
            intent="recognition_meaning_review",
        )
    )
    step = next(
        step for step in plan.steps
        if step.stage is ReasoningStage.RECOGNITION_MEANING
    )
    assert step.inputs == (
        "recognition_graph",
        "recognition_patterns",
        "delta_comparisons",
        "reflexive_graph",
        "reflexive_relations",
        "reflexive_loops",
    )
    assert step.outputs == (
        "recognition_meaning_graph",
        "recognition_meanings",
        "recognition_gaps",
        "recognition_completeness",
        "recognition_stability",
    )
