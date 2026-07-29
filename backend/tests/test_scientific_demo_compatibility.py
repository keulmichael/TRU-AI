from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from tru_ai.api.main import app as main_app
from tru_ai.cognitive.reasoning.models import (
    FalsificationReport,
    OperatorStatus,
    OperatorTrace,
    ReasoningPlan,
    ReasoningStage,
    ReasoningStep,
    ScientificGap,
    ScientificObservation,
    ScientificPrediction,
    ScientificTheoryRevision,
    VerificationReport,
    VerificationStatus,
)
from tru_ai.reasoning import api
from tru_ai.scientific.models import (
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
    ScientificStageCard,
    ScientificSummary,
    ScientificTheoryRevisionRecommendation,
)


def execution_plan() -> ReasoningPlan:
    return ReasoningPlan(
        question="Demo.",
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


def prediction(prediction_id: str) -> ScientificPrediction:
    return ScientificPrediction(
        prediction_id=prediction_id,
        text=f"Prediction {prediction_id}",
        source_claim_ids=("c1",),
        falsification_condition="Contradictory observation.",
        confidence=0.8,
        expected_observation="Expected observation.",
    )


def observation(observation_id: str, prediction_id: str) -> ScientificObservation:
    return ScientificObservation(
        observation_id=observation_id,
        text=f"Observation {observation_id}",
        prediction_id=prediction_id,
        compatibility_score=0.1,
        matches_falsification_condition=True,
    )


def raw_result() -> dict:
    plan = execution_plan()
    predictions = [prediction("p1").to_dict(), prediction("p2").to_dict()]
    observations = [
        observation("o1", "p1").to_dict(),
        observation("o2", "p2").to_dict(),
    ]
    verifications = [
        VerificationReport(
            report_id="v1",
            prediction_id="p1",
            observation_ids=("o1",),
            status=VerificationStatus.CONTRADICTED,
            consistency_score=0.1,
            evidence_score=0.5,
        ).to_dict(),
        VerificationReport(
            report_id="v2",
            prediction_id="p2",
            observation_ids=("o2",),
            status=VerificationStatus.CONFIRMED,
            consistency_score=0.9,
            evidence_score=0.5,
        ).to_dict(),
    ]
    falsifications = [
        FalsificationReport(
            report_id="f1",
            prediction_id="p1",
            verification_report_id="v1",
            falsified=True,
            formal_test_possible=True,
            falsification_condition_met=True,
            revision_required=True,
        ).to_dict(),
        FalsificationReport(
            report_id="f2",
            prediction_id="p2",
            verification_report_id="v2",
            falsified=False,
            formal_test_possible=True,
            revision_required=False,
        ).to_dict(),
    ]
    revisions = [
        ScientificTheoryRevision(
            revision_id="r1",
            prediction_id="p1",
            action="revise",
            reason="Contradicted.",
        ).to_dict(),
        ScientificTheoryRevision(
            revision_id="r2",
            prediction_id="p2",
            action="retain",
            reason="Confirmed.",
        ).to_dict(),
    ]
    gaps = [
        ScientificGap(gap_id="g1", description="Gap 1.").to_dict(),
        ScientificGap(gap_id="g2", description="Gap 2.").to_dict(),
    ]
    return {
        "plan": plan.to_dict(),
        "theory": {"maturity": {"score": 0.5}},
        "theory_graph": {
            "claims": [
                {"claim_id": "c1", "text": "Claim 1."},
                {"claim_id": "c2", "text": "Claim 2."},
            ]
        },
        "theory_evolution": {
            "added_claims": ["Claim 2."],
            "removed_claims": [],
            "strengthened_claims": [],
            "weakened_claims": [],
        },
        "theory_history": {"current_snapshot_id": "theory@0.9.5"},
        "scientific_predictions": predictions,
        "scientific_scenarios": [],
        "scenario_simulations": [],
        "scientific_observations": observations,
        "verification_reports": verifications,
        "falsification_reports": falsifications,
        "scientific_theory_revisions": revisions,
        "scientific_gaps": gaps,
        "operator_trace": [
            OperatorTrace(
                operator="ObservationOperator",
                stage=ReasoningStage.OBSERVATION,
                position=1,
                status=OperatorStatus.SUCCESS,
            ).to_dict(),
            OperatorTrace(
                operator="PredictionOperator",
                stage=ReasoningStage.PREDICTION,
                position=2,
                status=OperatorStatus.SUCCESS,
            ).to_dict(),
        ],
    }


def analysis_result() -> ScientificAnalysisResult:
    revision = ScientificTheoryRevision(
        revision_id="r1",
        prediction_id="p1",
        action="revise",
    )
    return ScientificAnalysisResult(
        analysis_id="analysis-demo",
        execution_plan=execution_plan(),
        summary=ScientificSummary(prediction_count=2, observation_count=2),
        stage_cards=[
            ScientificStageCard(
                stage="observation",
                title="Observation",
                status="success",
                summary="Generic observation card.",
            )
        ],
        scientific_predictions=[prediction("p1"), prediction("p2")],
        scientific_observations=[observation("o1", "p1"), observation("o2", "p2")],
        scientific_theory_revisions=[
            ScientificTheoryRevisionRecommendation(revision=revision)
        ],
        raw_result=raw_result(),
    )


class FakeScientificService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.requests: list[ScientificAnalysisRequest] = []

    def analyze(
        self,
        request: ScientificAnalysisRequest,
    ) -> ScientificAnalysisResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return analysis_result()


def create_client(
    service: FakeScientificService,
    monkeypatch: MonkeyPatch,
) -> TestClient:
    api.get_scientific_demo_service.cache_clear()
    monkeypatch.setattr(api, "get_scientific_demo_service", lambda: service)
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app)


def test_scientific_demo_page_remains_available() -> None:
    response = TestClient(main_app).get("/scientific-demo")

    assert response.status_code == 200


def test_scientific_demo_minimal_request_uses_scientific_service(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    response = client.post("/reasoning/scientific-demo", json={})

    assert response.status_code == 200
    assert len(service.requests) == 1
    request = service.requests[0]
    assert request.options.include_human_readable is True
    assert request.options.include_raw_result is True
    assert request.options.persist is False
    assert request.intent == "scientific_research"


def test_scientific_demo_complete_request_is_adapted(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    response = client.post(
        "/reasoning/scientific-demo",
        json={
            "observation": "Observed contradiction.",
            "claims": ["Claim one.", "Claim two."],
            "prediction_rule": {
                "id": "rule-1",
                "statement": "Prediction statement.",
                "condition": "condition",
                "consequence": "consequence",
                "confidence": 0.8,
            },
            "compatibility_score": 0.2,
            "matches_falsification_condition": True,
        },
    )

    assert response.status_code == 200
    request = service.requests[0]
    assert request.theory is not None
    assert request.theory.claims[0].claim_id == "c1"
    assert request.prediction_rules[0].id == "rule-1"
    assert request.scientific_observations[0].text == "Observed contradiction."


def test_scientific_demo_does_not_expose_direct_planner_executor_calls() -> None:
    assert not hasattr(api, "CognitiveReasoningPlanner")
    assert not hasattr(api, "CognitiveReasoningExecutor")


def test_scientific_demo_preserves_legacy_response_contract(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    data = client.post("/reasoning/scientific-demo", json={}).json()

    assert set(data) >= {
        "execution_plan",
        "theory_evolution",
        "theory_history",
        "scientific_predictions",
        "scientific_scenarios",
        "scenario_simulations",
        "verification_reports",
        "falsification_reports",
        "scientific_theory_revisions",
        "scientific_gaps",
        "operator_trace",
        "summary",
        "human_readable",
        "stage_cards",
        "raw_result",
    }
    assert set(data["human_readable"]["reflexive_view"]) == {
        "observed",
        "recognized",
        "predicted",
        "confirmed_or_refuted_by",
        "learning",
    }
    assert {"operator", "status", "inputs", "outputs", "score", "decision"} <= (
        set(data["stage_cards"][0])
    )


def test_scientific_demo_preserves_multiple_scientific_outputs(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    data = client.post("/reasoning/scientific-demo", json={}).json()

    assert len(data["scientific_predictions"]) == 2
    assert len(data["scientific_observations"]) == 2
    assert len(data["verification_reports"]) == 2
    assert len(data["falsification_reports"]) == 2
    assert len(data["scientific_gaps"]) == 2
    assert data["scientific_theory_revisions"][0]["action"] == "revise"


def test_scientific_demo_keeps_revision_as_recommendation(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    data = client.post("/reasoning/scientific-demo", json={}).json()

    assert service.requests[0].options.persist is False
    assert data["scientific_theory_revisions"][0]["action"] == "revise"
    assert "applied" not in data["scientific_theory_revisions"][0]


def test_scientific_demo_preserves_statuses_and_legacy_summary(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    data = client.post("/reasoning/scientific-demo", json={}).json()

    assert data["summary"]["verification_status"] == "contradicted"
    assert data["summary"]["falsified"] is True
    assert data["summary"]["revision_required"] is True
    assert data["summary"]["final_action"] == "revise"


def test_scientific_demo_validation_error_is_422(
    monkeypatch: MonkeyPatch,
) -> None:
    client = create_client(FakeScientificService(), monkeypatch)

    response = client.post(
        "/reasoning/scientific-demo",
        json={"observation": ""},
    )

    assert response.status_code == 422


def test_scientific_demo_service_value_error_is_422(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService(error=ValueError("Invalid demo request."))
    client = create_client(service, monkeypatch)

    response = client.post("/reasoning/scientific-demo", json={})

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid demo request."


def test_scientific_demo_service_unexpected_error_is_500(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService(error=RuntimeError("boom"))
    client = create_client(service, monkeypatch)

    response = client.post("/reasoning/scientific-demo", json={})

    assert response.status_code == 500
    assert response.json()["detail"] == "Scientific demo analysis failed."


def test_generic_scientific_analyze_route_remains_registered() -> None:
    response = TestClient(main_app).get("/scientific/health")

    assert response.status_code == 200
    assert response.json()["scientific_service_available"] is True
