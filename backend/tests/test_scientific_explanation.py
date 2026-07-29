from __future__ import annotations

import copy

from tru_ai.cognitive.reasoning.models import (
    FalsificationReport,
    OperatorStatus,
    OperatorTrace,
    ReasoningPlan,
    ReasoningResult,
    ReasoningStage,
    ReasoningStep,
    ScientificGap,
    ScientificObservation,
    ScientificPrediction,
    ScientificTheoryRevision,
    TheoryClaim,
    TheoryClaimStatus,
    TheoryEvolution,
    TheoryGraph,
    VerificationReport,
    VerificationStatus,
)
from tru_ai.scientific import (
    ScientificAnalysisOptions,
    ScientificAnalysisRequest,
    ScientificExplanationService,
    ScientificService,
)
from tru_ai.scientific.models import ScientificHumanReadable


def claim(claim_id: str) -> TheoryClaim:
    return TheoryClaim(
        claim_id=claim_id,
        text=f"Claim {claim_id}",
        status=TheoryClaimStatus.SUPPORTED,
    )


def prediction(prediction_id: str, status: str = "untested") -> ScientificPrediction:
    return ScientificPrediction(
        prediction_id=prediction_id,
        text=f"Prediction {prediction_id}",
        source_claim_ids=("c1",),
        status=status,
        confidence=0.7,
        expected_observation=f"Expected {prediction_id}",
        falsification_condition=f"Falsify {prediction_id}",
    )


def observation(observation_id: str, prediction_id: str) -> ScientificObservation:
    return ScientificObservation(
        observation_id=observation_id,
        text=f"Observation {observation_id}",
        prediction_id=prediction_id,
        compatibility_score=0.5,
        matches_falsification_condition=True,
    )


def plan() -> ReasoningPlan:
    return ReasoningPlan(
        question="Analyze scientific result.",
        intent="scientific_research",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.OBSERVATION,
                objective="Observe supplied data.",
            ),
            ReasoningStep(
                position=2,
                stage=ReasoningStage.THEORY_EVOLUTION,
                objective="Compare theory versions.",
            ),
            ReasoningStep(
                position=3,
                stage=ReasoningStage.PREDICTION,
                objective="Project predictions.",
            ),
            ReasoningStep(
                position=4,
                stage=ReasoningStage.VERIFICATION,
                objective="Check observations.",
            ),
            ReasoningStep(
                position=5,
                stage=ReasoningStage.FALSIFICATION,
                objective="Evaluate falsification.",
            ),
            ReasoningStep(
                position=6,
                stage=ReasoningStage.SCIENTIFIC_GAPS,
                objective="Report scientific gaps.",
            ),
            ReasoningStep(
                position=7,
                stage=ReasoningStage.SYNTHESIS,
                objective="Synthesize actual results.",
            ),
        ),
    )


def trace(
    position: int,
    stage: ReasoningStage,
    operator: str,
) -> OperatorTrace:
    return OperatorTrace(
        operator=operator,
        stage=stage,
        position=position,
        status=OperatorStatus.SUCCESS,
        inputs=(f"input-{position}",),
        outputs=(f"output-{position}",),
    )


def rich_result() -> ReasoningResult:
    return ReasoningResult(
        plan=plan(),
        theory_graph=TheoryGraph(
            theory_id="theory-a",
            name="Theory A",
            claims=(claim("c1"), claim("c2")),
        ),
        theory_evolution=TheoryEvolution(
            added_claims=("c2",),
            weakened_claims=("c1",),
        ),
        operator_trace=(
            trace(1, ReasoningStage.OBSERVATION, "ObservationOperator"),
            trace(2, ReasoningStage.THEORY_EVOLUTION, "TheoryEvolutionOperator"),
            trace(3, ReasoningStage.PREDICTION, "PredictionOperator"),
            trace(4, ReasoningStage.VERIFICATION, "VerificationOperator"),
            trace(5, ReasoningStage.FALSIFICATION, "FalsificationOperator"),
            trace(6, ReasoningStage.SCIENTIFIC_GAPS, "ScientificGapsOperator"),
            trace(7, ReasoningStage.SYNTHESIS, "SynthesisOperator"),
        ),
        scientific_predictions=(
            prediction("p1", status="untested"),
            prediction("p2", status="retained"),
        ),
        scientific_observations=(
            observation("o1", "p1"),
            observation("o2", "p2"),
        ),
        verification_reports=(
            VerificationReport(
                report_id="v1",
                prediction_id="p1",
                observation_ids=("o1",),
                status=VerificationStatus.CONFIRMED,
                consistency_score=0.9,
                evidence_score=0.8,
                rationale="Confirmed by observation.",
                limitations=("limited sample",),
            ),
            VerificationReport(
                report_id="v2",
                prediction_id="p2",
                observation_ids=("o2",),
                status=VerificationStatus.CONTRADICTED,
                consistency_score=0.1,
                evidence_score=0.7,
                rationale="Contradicted by observation.",
            ),
            VerificationReport(
                report_id="v3",
                prediction_id="p3",
                status=VerificationStatus.INCONCLUSIVE,
            ),
        ),
        falsification_reports=(
            FalsificationReport(
                report_id="f1",
                prediction_id="p1",
                verification_report_id="v1",
                falsified=False,
                formal_test_possible=True,
                revision_required=False,
            ),
            FalsificationReport(
                report_id="f2",
                prediction_id="p2",
                verification_report_id="v2",
                falsified=True,
                falsification_condition_met=True,
                revision_required=True,
                rationale="Falsification condition matched.",
            ),
        ),
        scientific_theory_revisions=(
            ScientificTheoryRevision(
                revision_id="r1",
                prediction_id="p2",
                action="revise",
                reason="Contradiction requires revision recommendation.",
            ),
            ScientificTheoryRevision(
                revision_id="r2",
                prediction_id="p1",
                action="retain",
                reason="Confirmation supports retention recommendation.",
            ),
        ),
        scientific_gaps=(
            ScientificGap(
                gap_id="g1",
                description="Missing replicated observation.",
                required_action="collect_observation",
            ),
            ScientificGap(
                gap_id="g2",
                description="Missing independent verification.",
            ),
        ),
        synthesis="Synthesis from actual results.",
    )


class RecordingPlanner:
    def plan(self, request):
        return plan()


class RecordingExecutor:
    def __init__(self, selected_result: ReasoningResult) -> None:
        self.selected_result = selected_result

    def execute(self, selected_plan, *, conversation_context=None):
        return self.selected_result


def test_empty_result_produces_no_invented_explanation() -> None:
    result = ReasoningResult(
        plan=ReasoningPlan(
            question="Analyze.",
            intent="scientific_research",
            steps=(),
        )
    )
    service = ScientificExplanationService()

    summary = service.summary(result)
    readable = service.human_readable(result)
    cards = service.stage_cards(result)

    assert summary.claim_count == 0
    assert summary.prediction_count == 0
    assert summary.observation_count == 0
    assert summary.verification_report_count == 0
    assert summary.falsification_report_count == 0
    assert summary.has_theory_evolution is False
    assert summary.has_revision_recommendations is False
    assert readable == ScientificHumanReadable()
    assert cards == []


def test_summary_counts_actual_scientific_outputs() -> None:
    summary = ScientificExplanationService().summary(rich_result())

    assert summary.claim_count == 2
    assert summary.prediction_count == 2
    assert summary.observation_count == 2
    assert summary.verification_report_count == 3
    assert summary.verification_status_counts == {
        "confirmed": 1,
        "contradicted": 1,
        "inconclusive": 1,
    }
    assert summary.falsification_report_count == 2
    assert summary.falsified_count == 1
    assert summary.scientific_gap_count == 2
    assert summary.has_theory_evolution is True
    assert summary.has_revision_recommendations is True
    assert summary.revision_recommendation_count == 2


def test_human_readable_keeps_multiple_predictions_and_observations() -> None:
    readable = ScientificExplanationService().human_readable(rich_result())

    assert len(readable.predictions) == 2
    assert "p1" in readable.predictions[0]
    assert "p2" in readable.predictions[1]
    assert len(readable.observations) == 2
    assert "o1" in readable.observations[0]
    assert "o2" in readable.observations[1]
    assert readable.overview == "Synthesis from actual results."


def test_human_readable_keeps_multiple_reports_gaps_and_revisions() -> None:
    readable = ScientificExplanationService().human_readable(rich_result())

    assert len(readable.verification_reports) == 3
    assert "status=confirmed" in readable.verification_reports[0]
    assert "status=contradicted" in readable.verification_reports[1]
    assert "status=inconclusive" in readable.verification_reports[2]
    assert len(readable.falsification_reports) == 2
    assert "falsified=False" in readable.falsification_reports[0]
    assert "falsified=True" in readable.falsification_reports[1]
    assert len(readable.scientific_gaps) == 2
    assert "g1" in readable.scientific_gaps[0]
    assert "g2" in readable.scientific_gaps[1]
    assert len(readable.revision_recommendations) == 2
    assert "recommended_action=revise" in readable.revision_recommendations[0]
    assert "applied=False" in readable.revision_recommendations[0]
    assert "recommended_action=retain" in readable.revision_recommendations[1]


def test_statuses_are_preserved_without_new_status_invention() -> None:
    readable = ScientificExplanationService().human_readable(rich_result())
    joined = "\n".join(
        readable.predictions
        + readable.verification_reports
        + readable.revision_recommendations
    )

    assert "status=untested" in joined
    assert "status=retained" in joined
    assert "status=confirmed" in joined
    assert "status=contradicted" in joined
    assert "status=inconclusive" in joined
    assert "recommended_action=revise" in joined
    assert "recommended_action=retain" in joined


def test_stage_cards_follow_actual_operator_trace() -> None:
    cards = ScientificExplanationService().stage_cards(rich_result())

    assert [card.stage for card in cards] == [
        "observation",
        "theory_evolution",
        "prediction",
        "verification",
        "falsification",
        "scientific_gaps",
        "synthesis",
    ]
    assert cards[0].details["operator"] == "ObservationOperator"
    assert cards[2].data["scientific_predictions"][1]["prediction_id"] == "p2"
    assert cards[-1].data["synthesis"] == "Synthesis from actual results."


def test_stage_cards_do_not_add_unexecuted_plan_steps() -> None:
    selected_plan = ReasoningPlan(
        question="Analyze.",
        intent="scientific_research",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.OBSERVATION,
                objective="Observe.",
            ),
            ReasoningStep(
                position=2,
                stage=ReasoningStage.PREDICTION,
                objective="Predict.",
            ),
        ),
    )
    result = ReasoningResult(
        plan=selected_plan,
        operator_trace=(
            trace(1, ReasoningStage.OBSERVATION, "ObservationOperator"),
        ),
    )

    cards = ScientificExplanationService().stage_cards(result)

    assert [card.stage for card in cards] == ["observation"]


def test_explanation_service_does_not_mutate_reasoning_result() -> None:
    result = rich_result()
    before = copy.deepcopy(result.to_dict())
    service = ScientificExplanationService()

    service.summary(result)
    service.human_readable(result)
    service.stage_cards(result)

    assert result.to_dict() == before


def test_explanation_models_are_serializable() -> None:
    service = ScientificExplanationService()
    result = rich_result()

    summary, readable, cards = service.explain(result)

    assert summary.model_dump(mode="json")["prediction_count"] == 2
    assert readable.model_dump(mode="json")["predictions"][1]
    assert cards[0].model_dump(mode="json")["stage"] == "observation"


def test_scientific_service_builds_explanation_when_requested() -> None:
    request = ScientificAnalysisRequest(
        question="Analyze.",
        options=ScientificAnalysisOptions(include_human_readable=True),
    )
    service = ScientificService(
        planner=RecordingPlanner(),
        executor=RecordingExecutor(rich_result()),
    )

    response = service.analyze(request)

    assert response.human_readable is not None
    assert len(response.human_readable.predictions) == 2
    assert len(response.stage_cards) == 7


def test_scientific_service_skips_human_readable_when_disabled() -> None:
    request = ScientificAnalysisRequest(
        question="Analyze.",
        options=ScientificAnalysisOptions(include_human_readable=False),
    )
    service = ScientificService(
        planner=RecordingPlanner(),
        executor=RecordingExecutor(rich_result()),
    )

    response = service.analyze(request)

    assert response.human_readable is None
    assert response.stage_cards == []
    assert response.summary.prediction_count == 2
