from __future__ import annotations

import pytest
from pydantic import ValidationError

from tru_ai.cognitive.reasoning.models import (
    ReasoningPlan,
    ReasoningStage,
    ReasoningStep,
    ScientificObservation,
    ScientificPrediction,
    ScientificScenario,
    ScientificTheoryRevision,
    TheoryClaim,
    TheoryClaimStatus,
    VerificationStatus,
)
from tru_ai.scientific import (
    ScientificAnalysisOptions,
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
    ScientificBaselineInput,
    ScientificHumanReadable,
    ScientificPredictionRuleInput,
    ScientificStageCard,
    ScientificSummary,
    ScientificTheoryInput,
    ScientificTheoryRevisionRecommendation,
)


def claim(claim_id: str = "c1") -> TheoryClaim:
    return TheoryClaim(
        claim_id=claim_id,
        text=f"Claim {claim_id}",
        status=TheoryClaimStatus.PARTIAL,
    )


def prediction(prediction_id: str) -> ScientificPrediction:
    return ScientificPrediction(
        prediction_id=prediction_id,
        text=f"Prediction {prediction_id}",
        source_claim_ids=("c1",),
    )


def observation(observation_id: str) -> ScientificObservation:
    return ScientificObservation(
        observation_id=observation_id,
        text=f"Observation {observation_id}",
        prediction_id="p1",
    )


def test_minimal_scientific_analysis_request_defaults() -> None:
    request = ScientificAnalysisRequest(question="Analyze this theory.")

    assert request.intent == "scientific_research"
    assert request.options.include_raw_result is False
    assert request.options.include_human_readable is True
    assert request.options.persist is False
    assert request.predictions == []
    assert request.scientific_observations == []


def test_complete_scientific_analysis_request_serializes() -> None:
    request = ScientificAnalysisRequest(
        question="Compare this theory with observations.",
        theory_version="0.9.6",
        theory=ScientificTheoryInput(
            id="theory-a",
            name="Theory A",
            claims=[claim()],
            relations=[("c1", "supports", "c2")],
        ),
        baseline_theory=ScientificBaselineInput(claims=[claim("b1")]),
        comparison_theories=[
            ScientificTheoryInput(
                id="theory-b",
                name="Theory B",
                claims=[claim("c2")],
            )
        ],
        predictions=[prediction("p1"), prediction("p2")],
        prediction_rules=[
            ScientificPredictionRuleInput(
                id="rule-1",
                condition="condition",
                consequence="consequence",
                source_claim_ids=["c1"],
                confidence=0.8,
            )
        ],
        scenarios=[
            ScientificScenario(
                scenario_id="s1",
                name="Scenario 1",
                assumptions=("condition",),
            )
        ],
        scientific_observations=[observation("o1"), observation("o2")],
        options=ScientificAnalysisOptions(include_raw_result=True),
    )

    payload = request.model_dump(mode="json")

    assert payload["theory"]["id"] == "theory-a"
    assert payload["theory"]["claims"][0]["claim_id"] == "c1"
    assert payload["prediction_rules"][0]["consequence"] == "consequence"
    assert len(payload["predictions"]) == 2
    assert len(payload["scientific_observations"]) == 2
    assert payload["options"]["include_raw_result"] is True


def test_scientific_analysis_request_deserializes() -> None:
    request = ScientificAnalysisRequest.model_validate(
        {
            "question": "Analyze.",
            "theory": {
                "id": "theory-a",
                "name": "Theory A",
                "claims": [
                    {
                        "claim_id": "c1",
                        "text": "Claim c1",
                        "status": "supported",
                    }
                ],
            },
            "predictions": [
                {
                    "prediction_id": "p1",
                    "text": "Prediction p1",
                    "source_claim_ids": ["c1"],
                }
            ],
            "scientific_observations": [
                {
                    "observation_id": "o1",
                    "text": "Observation o1",
                    "prediction_id": "p1",
                }
            ],
        }
    )

    assert isinstance(request.theory, ScientificTheoryInput)
    assert isinstance(request.theory.claims[0], TheoryClaim)
    assert isinstance(request.predictions[0], ScientificPrediction)
    assert isinstance(request.scientific_observations[0], ScientificObservation)


def test_invalid_structures_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ScientificAnalysisRequest(question="")

    with pytest.raises(ValidationError):
        ScientificTheoryInput(id="", name="Theory", claims=[])

    with pytest.raises(ValidationError):
        ScientificBaselineInput()

    with pytest.raises(ValidationError):
        ScientificPredictionRuleInput(
            id="rule-1",
            condition="condition",
            consequence="consequence",
            confidence=1.2,
        )


def test_default_lists_are_independent() -> None:
    first = ScientificAnalysisRequest(question="First.")
    second = ScientificAnalysisRequest(question="Second.")

    first.predictions.append(prediction("p1"))
    first.scientific_observations.append(observation("o1"))

    assert second.predictions == []
    assert second.scientific_observations == []


def test_human_readable_preserves_multiple_items() -> None:
    readable = ScientificHumanReadable(
        predictions=["prediction one", "prediction two"],
        observations=["observation one", "observation two"],
        verification_reports=[
            VerificationStatus.CONFIRMED.value,
            VerificationStatus.CONTRADICTED.value,
        ],
    )

    assert readable.predictions == ["prediction one", "prediction two"]
    assert readable.observations == ["observation one", "observation two"]
    assert len(readable.verification_reports) == 2


def test_raw_result_is_absent_from_serialized_output_by_default() -> None:
    plan = ReasoningPlan(
        question="Analyze.",
        intent="scientific_research",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.OBSERVATION,
                objective="Observe",
            ),
        ),
    )
    result = ScientificAnalysisResult(
        analysis_id="analysis-1",
        execution_plan=plan,
        summary=ScientificSummary(prediction_count=2),
        stage_cards=[
            ScientificStageCard(
                stage="prediction",
                title="Prediction",
                status="success",
            )
        ],
        scientific_predictions=[prediction("p1"), prediction("p2")],
        scientific_observations=[observation("o1"), observation("o2")],
    )

    payload = result.model_dump(mode="json", exclude_none=True)

    assert "raw_result" not in payload
    assert payload["execution_plan"]["intent"] == "scientific_research"
    assert len(payload["scientific_predictions"]) == 2
    assert len(payload["scientific_observations"]) == 2


def test_revision_recommendation_is_not_presented_as_applied() -> None:
    recommendation = ScientificTheoryRevisionRecommendation(
        revision=ScientificTheoryRevision(
            revision_id="r1",
            prediction_id="p1",
            action="revise",
            reason="Observation contradicted prediction.",
        )
    )

    assert recommendation.applied is False
    assert recommendation.model_dump(mode="json")["applied"] is False

    with pytest.raises(ValidationError):
        ScientificTheoryRevisionRecommendation.model_validate(
            {
                "revision": {
                    "revision_id": "r1",
                    "prediction_id": "p1",
                    "action": "revise",
                },
                "applied": True,
            }
        )


def test_public_theory_input_reuses_internal_theory_graph() -> None:
    theory = ScientificTheoryInput(
        id="theory-a",
        name="Theory A",
        claims=[claim()],
        relations=[("c1", "supports", "c2")],
    )

    graph = theory.to_theory_graph()

    assert graph.theory_id == "theory-a"
    assert graph.name == "Theory A"
    assert graph.claims == (claim(),)
    assert graph.relations == (("c1", "supports", "c2"),)
