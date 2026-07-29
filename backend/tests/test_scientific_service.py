from __future__ import annotations

import copy
from typing import Any

from tru_ai.cognitive.reasoning.models import (
    FalsificationReport,
    OperatorStatus,
    OperatorTrace,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStage,
    ReasoningStep,
    ScientificGap,
    ScientificObservation,
    ScientificPrediction,
    ScientificScenario,
    ScientificTheoryRevision,
    TheoryClaim,
    TheoryClaimStatus,
    VerificationReport,
    VerificationStatus,
)
from tru_ai.scientific import (
    ScientificAnalysisOptions,
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
    ScientificBaselineInput,
    ScientificInputAdapter,
    ScientificPredictionRuleInput,
    ScientificService,
    ScientificTheoryInput,
)


def claim(claim_id: str = "c1") -> TheoryClaim:
    return TheoryClaim(
        claim_id=claim_id,
        text=f"Claim {claim_id}",
        status=TheoryClaimStatus.SUPPORTED,
        evidence=("e1",),
        confidence=0.8,
    )


def prediction(prediction_id: str = "p1") -> ScientificPrediction:
    return ScientificPrediction(
        prediction_id=prediction_id,
        text=f"Prediction {prediction_id}",
        source_claim_ids=("c1",),
        expected_observation="Expected observation.",
        falsification_condition="Contradictory observation.",
        confidence=0.7,
    )


def observation(observation_id: str = "o1") -> ScientificObservation:
    return ScientificObservation(
        observation_id=observation_id,
        text=f"Observation {observation_id}",
        prediction_id="p1",
        compatibility_score=0.9,
    )


def plan() -> ReasoningPlan:
    return ReasoningPlan(
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


def result(reasoning_plan: ReasoningPlan | None = None) -> ReasoningResult:
    selected_plan = reasoning_plan or plan()
    return ReasoningResult(
        plan=selected_plan,
        operator_trace=(
            OperatorTrace(
                operator="ObservationOperator",
                stage=ReasoningStage.OBSERVATION,
                position=1,
                status=OperatorStatus.SUCCESS,
            ),
        ),
        scientific_predictions=(prediction("p1"), prediction("p2")),
        scientific_scenarios=(
            ScientificScenario(
                scenario_id="s1",
                name="Scenario 1",
                assumptions=("condition",),
            ),
        ),
        scientific_observations=(observation("o1"), observation("o2")),
        verification_reports=(
            VerificationReport(
                report_id="v1",
                prediction_id="p1",
                status=VerificationStatus.CONFIRMED,
            ),
        ),
        falsification_reports=(
            FalsificationReport(
                report_id="f1",
                prediction_id="p1",
                verification_report_id="v1",
                falsified=False,
            ),
        ),
        scientific_theory_revisions=(
            ScientificTheoryRevision(
                revision_id="r1",
                prediction_id="p1",
                action="retain",
            ),
        ),
        scientific_gaps=(
            ScientificGap(
                gap_id="g1",
                description="Missing replicated observation.",
            ),
        ),
        synthesis="Synthesis from actual reasoning result.",
    )


class RecordingPlanner:
    def __init__(self, selected_plan: ReasoningPlan | None = None) -> None:
        self.selected_plan = selected_plan or plan()
        self.requests: list[ReasoningRequest] = []

    def plan(self, request: ReasoningRequest) -> ReasoningPlan:
        self.requests.append(request)
        return self.selected_plan


class RecordingExecutor:
    def __init__(self, selected_result: ReasoningResult | None = None) -> None:
        self.selected_result = selected_result
        self.calls: list[tuple[ReasoningPlan, dict[str, Any]]] = []

    def execute(
        self,
        plan: ReasoningPlan,
        *,
        conversation_context: dict[str, Any] | None = None,
    ) -> ReasoningResult:
        context = dict(conversation_context or {})
        self.calls.append((plan, dict(context)))
        context["executor_mutation"] = True
        return self.selected_result or result(plan)


def full_request() -> ScientificAnalysisRequest:
    return ScientificAnalysisRequest(
        question="Analyze public scientific inputs.",
        theory_version="0.9.6-dev",
        theory=ScientificTheoryInput(
            id="theory-a",
            name="Theory A",
            claims=[claim("c1")],
            relations=[("c1", "c2", "supports")],
        ),
        baseline_theory=ScientificBaselineInput(claims=[claim("b1")]),
        comparison_theories=[
            ScientificTheoryInput(
                id="theory-b",
                name="Theory B",
                claims=[claim("c2")],
            )
        ],
        predictions=[prediction("p1")],
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
        scientific_observations=[observation("o1")],
        options=ScientificAnalysisOptions(
            include_raw_result=True,
            include_human_readable=True,
            persist=False,
        ),
    )


def test_adapter_maps_minimal_request_to_empty_context() -> None:
    request = ScientificAnalysisRequest(question="Analyze.")

    context = ScientificInputAdapter().to_conversation_context(request)

    assert context == {}


def test_adapter_maps_complete_request_without_inventing_keys() -> None:
    context = ScientificInputAdapter().to_conversation_context(full_request())

    assert context["theory_version"] == "0.9.6-dev"
    assert context["theory"]["id"] == "theory-a"
    assert context["theory"]["claims"][0]["claim_id"] == "c1"
    assert context["theory"]["relations"] == [
        {"source": "c1", "target": "c2", "type": "supports"}
    ]
    assert context["baseline_theory"]["claims"][0]["claim_id"] == "b1"
    assert context["comparison_theories"][0]["id"] == "theory-b"
    assert context["predictions"][0]["prediction_id"] == "p1"
    assert context["prediction_rules"][0]["if"] == "condition"
    assert context["prediction_rules"][0]["then"] == "consequence"
    assert context["scenarios"][0]["scenario_id"] == "s1"
    assert context["scientific_observations"][0]["observation_id"] == "o1"
    assert "persist" not in context


def test_service_accepts_minimal_request_and_calls_pipeline() -> None:
    planner = RecordingPlanner()
    executor = RecordingExecutor()
    service = ScientificService(planner=planner, executor=executor)

    response = service.analyze(
        ScientificAnalysisRequest(question="Analyze minimal request.")
    )

    assert isinstance(response, ScientificAnalysisResult)
    assert planner.requests[0].question == "Analyze minimal request."
    assert planner.requests[0].intent == "scientific_research"
    assert executor.calls[0][1] == {}
    assert response.raw_result is None
    assert response.summary.prediction_count == 2


def test_service_maps_complete_request_and_projects_result() -> None:
    planner = RecordingPlanner()
    executor = RecordingExecutor()
    service = ScientificService(planner=planner, executor=executor)

    response = service.analyze(full_request())

    context = executor.calls[0][1]
    assert context["theory"]["id"] == "theory-a"
    assert context["prediction_rules"][0]["if"] == "condition"
    assert response.raw_result is not None
    assert response.human_readable is not None
    assert response.human_readable.overview == (
        "Synthesis from actual reasoning result."
    )
    assert len(response.scientific_predictions) == 2
    assert len(response.scientific_observations) == 2
    assert response.verification_reports[0].status is VerificationStatus.CONFIRMED
    assert response.scientific_theory_revisions[0].applied is False
    assert response.summary.verification_status_counts == {"confirmed": 1}
    assert response.summary.revision_recommendation_count == 1


def test_service_does_not_mutate_request_data() -> None:
    request = full_request()
    before = copy.deepcopy(request.model_dump(mode="json"))
    service = ScientificService(
        planner=RecordingPlanner(),
        executor=RecordingExecutor(),
    )

    service.analyze(request)

    assert request.model_dump(mode="json") == before


def test_service_keeps_persist_false_as_non_runtime_option() -> None:
    request = full_request()
    request.options.persist = False
    executor = RecordingExecutor()
    service = ScientificService(
        planner=RecordingPlanner(),
        executor=executor,
    )

    response = service.analyze(request)

    assert request.options.persist is False
    assert "persist" not in executor.calls[0][1]
    assert response.raw_result is not None


def test_service_is_compatible_with_public_models() -> None:
    response = ScientificService(
        planner=RecordingPlanner(),
        executor=RecordingExecutor(),
    ).analyze(full_request())

    payload = response.model_dump(mode="json", exclude_none=True)

    assert payload["execution_plan"]["intent"] == "scientific_research"
    assert payload["scientific_predictions"][0]["prediction_id"] == "p1"
    assert payload["scientific_observations"][0]["observation_id"] == "o1"
    assert payload["scientific_theory_revisions"][0]["applied"] is False
