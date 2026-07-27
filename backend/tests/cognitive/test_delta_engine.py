from __future__ import annotations

from tru_ai.cognitive.reasoning import (
    DeltaDirection,
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
    ReasoningStage,
)


def build_plan(intent: str = "delta_review"):
    return ReasoningPlanner().plan(
        ReasoningRequest(
            question="Analyse le Delta.",
            intent=intent,
        )
    )


def test_delta_review_contains_delta_stage() -> None:
    plan = build_plan()
    assert ReasoningStage.DELTA in tuple(step.stage for step in plan.steps)
    assert tuple(step.stage for step in plan.steps).index(
        ReasoningStage.RECOGNITION
    ) < tuple(step.stage for step in plan.steps).index(ReasoningStage.DELTA)


def test_delta_engine_calculates_predicted_minus_start() -> None:
    result = ReasoningExecutor().execute(
        build_plan(),
        conversation_context={
            "delta_comparisons": [
                {
                    "id": "energy",
                    "dimension": "energy",
                    "start_state": 4,
                    "predicted_state": 7,
                    "desired_state": 10,
                    "observed_state": 6,
                    "evidence": ["Mesure initiale", "Prévision déclarée"],
                }
            ]
        },
    )

    comparison = result.delta_comparisons[0]
    assert comparison.delta_value == 3.0
    assert comparison.direction == DeltaDirection.INCREASE
    assert comparison.desired_state == 10
    assert comparison.observed_state == 6


def test_delta_engine_does_not_replace_prediction_with_desire() -> None:
    result = ReasoningExecutor().execute(
        build_plan(),
        conversation_context={
            "delta_comparisons": [
                {
                    "id": "trajectory",
                    "dimension": "trajectory",
                    "start_state": 10,
                    "predicted_state": 8,
                    "desired_state": 20,
                }
            ]
        },
    )

    comparison = result.delta_comparisons[0]
    assert comparison.delta_value == -2.0
    assert comparison.direction == DeltaDirection.DECREASE


def test_non_numeric_states_are_preserved_without_invented_value() -> None:
    result = ReasoningExecutor().execute(
        build_plan(),
        conversation_context={
            "delta_comparisons": [
                {
                    "id": "status",
                    "dimension": "status",
                    "start_state": "latent",
                    "predicted_state": "recognized",
                }
            ]
        },
    )

    comparison = result.delta_comparisons[0]
    assert comparison.delta_value is None
    assert comparison.direction == DeltaDirection.UNDETERMINED
    assert comparison.limitations


def test_invalid_or_incomplete_comparisons_are_ignored() -> None:
    result = ReasoningExecutor().execute(
        build_plan(),
        conversation_context={
            "delta_comparisons": [
                {"id": "missing-prediction", "start_state": 1},
                "invalid",
            ]
        },
    )
    assert result.delta_comparisons == ()


def test_delta_is_json_serializable() -> None:
    payload = ReasoningExecutor().execute(
        build_plan(),
        conversation_context={
            "delta_comparisons": [
                {
                    "id": "temperature",
                    "dimension": "temperature",
                    "start_state": 18,
                    "predicted_state": 18,
                }
            ]
        },
    ).to_dict()

    assert payload["delta_comparisons"][0]["direction"] == "stable"
    assert payload["delta_comparisons"][0]["delta_value"] == 0.0
