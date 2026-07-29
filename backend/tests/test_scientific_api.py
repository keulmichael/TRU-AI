from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from tru_ai import __version__
from tru_ai.api.main import app as main_app
from tru_ai.cognitive.reasoning.models import (
    ReasoningPlan,
    ReasoningStage,
    ReasoningStep,
    ScientificObservation,
    ScientificPrediction,
    ScientificScenario,
    TheoryClaim,
    TheoryClaimStatus,
)
from tru_ai.scientific import api
from tru_ai.scientific.models import (
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
    ScientificSummary,
)


def claim(claim_id: str = "c1") -> TheoryClaim:
    return TheoryClaim(
        claim_id=claim_id,
        text=f"Claim {claim_id}",
        status=TheoryClaimStatus.SUPPORTED,
    )


def prediction(prediction_id: str = "p1") -> ScientificPrediction:
    return ScientificPrediction(
        prediction_id=prediction_id,
        text=f"Prediction {prediction_id}",
        source_claim_ids=("c1",),
    )


def observation(observation_id: str = "o1") -> ScientificObservation:
    return ScientificObservation(
        observation_id=observation_id,
        text=f"Observation {observation_id}",
        prediction_id="p1",
    )


def execution_plan() -> ReasoningPlan:
    return ReasoningPlan(
        question="Analyze.",
        intent="scientific_research",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.OBSERVATION,
                objective="Observe.",
            ),
        ),
    )


def analysis_result(
    *,
    include_raw_result: bool = False,
) -> ScientificAnalysisResult:
    raw = {
        "plan": execution_plan().to_dict(),
        "scientific_predictions": [prediction().to_dict()],
    }
    return ScientificAnalysisResult(
        analysis_id="analysis-1",
        execution_plan=execution_plan(),
        summary=ScientificSummary(
            prediction_count=1,
            observation_count=1,
        ),
        scientific_predictions=[prediction()],
        scientific_scenarios=[
            ScientificScenario(
                scenario_id="s1",
                name="Scenario 1",
            )
        ],
        scientific_observations=[observation()],
        raw_result=raw if include_raw_result else None,
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
        return analysis_result(
            include_raw_result=request.options.include_raw_result
        )


def create_client(
    service: FakeScientificService | None = None,
    monkeypatch: MonkeyPatch | None = None,
) -> TestClient:
    api.get_scientific_service.cache_clear()
    if service is not None:
        if monkeypatch is None:
            raise ValueError("monkeypatch is required for fake service tests")

        def get_service() -> FakeScientificService:
            return service

        monkeypatch.setattr(api, "get_scientific_service", get_service)
        app = FastAPI()
        app.include_router(api.router)
        return TestClient(app)

    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app)


def test_scientific_health() -> None:
    client = create_client()

    response = client.get("/scientific/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": __version__,
        "scientific_service_available": True,
        "planner_available": True,
        "executor_available": True,
    }


def test_scientific_router_is_registered_on_main_app() -> None:
    client = TestClient(main_app)

    response = client.get("/scientific/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scientific_analyze_minimal(monkeypatch: MonkeyPatch) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    response = client.post(
        "/scientific/analyze",
        json={"question": "Analyze this."},
    )

    assert response.status_code == 200
    data = response.json()
    assert service.requests[0].question == "Analyze this."
    assert service.requests[0].intent == "scientific_research"
    assert data["analysis_id"] == "analysis-1"
    assert data["summary"]["prediction_count"] == 1
    assert data["raw_result"] is None


def test_scientific_analyze_complete(monkeypatch: MonkeyPatch) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    response = client.post(
        "/scientific/analyze",
        json={
            "question": "Analyze complete request.",
            "theory_version": "0.9.6",
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
            "options": {
                "include_raw_result": True,
                "include_human_readable": True,
                "persist": False,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert service.requests[0].theory is not None
    assert service.requests[0].theory.id == "theory-a"
    assert data["raw_result"]["scientific_predictions"][0]["prediction_id"] == "p1"
    assert data["scientific_predictions"][0]["prediction_id"] == "p1"
    assert data["scientific_observations"][0]["observation_id"] == "o1"


def test_scientific_analyze_pydantic_validation_422(
    monkeypatch: MonkeyPatch,
) -> None:
    client = create_client(FakeScientificService(), monkeypatch)

    response = client.post(
        "/scientific/analyze",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_scientific_analyze_malformed_json_422(
    monkeypatch: MonkeyPatch,
) -> None:
    client = create_client(FakeScientificService(), monkeypatch)

    response = client.post(
        "/scientific/analyze",
        content="{",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


def test_scientific_analyze_service_value_error_400(
    monkeypatch: MonkeyPatch,
) -> None:
    client = create_client(
        FakeScientificService(error=ValueError("Invalid scientific request.")),
        monkeypatch,
    )

    response = client.post(
        "/scientific/analyze",
        json={"question": "Analyze."},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid scientific request."


def test_scientific_analyze_unexpected_error_500(
    monkeypatch: MonkeyPatch,
) -> None:
    client = create_client(
        FakeScientificService(error=RuntimeError("boom")),
        monkeypatch,
    )

    response = client.post(
        "/scientific/analyze",
        json={"question": "Analyze."},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Scientific analysis failed."


def test_scientific_analyze_serialization_and_raw_result_option(
    monkeypatch: MonkeyPatch,
) -> None:
    service = FakeScientificService()
    client = create_client(service, monkeypatch)

    response = client.post(
        "/scientific/analyze",
        json={
            "question": "Analyze.",
            "options": {"include_raw_result": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["execution_plan"]["intent"] == "scientific_research"
    assert data["raw_result"]["plan"]["intent"] == "scientific_research"
    assert data["scientific_scenarios"][0]["scenario_id"] == "s1"
