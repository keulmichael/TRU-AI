from __future__ import annotations

from fastapi.testclient import TestClient

from tru_ai import __version__
from tru_ai.api.main import app


client = TestClient(app)


def release_payload(*, include_raw_result: bool = False) -> dict:
    return {
        "question": "Analyze release scientific claim.",
        "theory_version": "0.9.6",
        "theory": {
            "id": "release-theory",
            "name": "Release Theory",
            "claims": [
                {
                    "claim_id": "c1",
                    "text": "Repeated recognition stabilizes a relation.",
                    "status": "supported",
                    "confidence": 0.8,
                }
            ],
        },
        "prediction_rules": [
            {
                "id": "rule-1",
                "condition": "recognition repeats",
                "consequence": "relation stability increases",
                "source_claim_ids": ["c1"],
                "confidence": 0.8,
                "expected_observation": "Observed stability increases.",
                "falsification_condition": "Observed stability decreases.",
            }
        ],
        "scientific_observations": [
            {
                "observation_id": "o1",
                "prediction_id": "rule-1",
                "text": "Observed stability increases.",
                "compatibility_score": 0.9,
                "matches_falsification_condition": False,
            }
        ],
        "options": {
            "include_raw_result": include_raw_result,
            "include_human_readable": True,
            "persist": False,
        },
    }


def test_scientific_health_reports_release_version() -> None:
    response = client.get("/scientific/health")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.9.6"
    assert data["version"] == __version__
    assert data["scientific_service_available"] is True
    assert data["planner_available"] is True
    assert data["executor_available"] is True


def test_scientific_analyze_minimal_release_chain() -> None:
    response = client.post(
        "/scientific/analyze",
        json={"question": "Analyze minimal release readiness."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["execution_plan"]["intent"] == "scientific_research"
    assert data["summary"]["claim_count"] >= 0
    assert data["summary"]["prediction_count"] >= 0
    assert data["human_readable"] is not None
    assert data["raw_result"] is None


def test_scientific_analyze_full_release_chain_without_raw_result() -> None:
    response = client.post(
        "/scientific/analyze",
        json=release_payload(include_raw_result=False),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["claim_count"] == 1
    assert data["summary"]["prediction_count"] == 1
    assert data["summary"]["observation_count"] == 1
    assert data["summary"]["verification_report_count"] == 1
    assert data["summary"]["falsification_report_count"] == 1
    assert data["scientific_predictions"][0]["prediction_id"] == "rule-1"
    assert data["scientific_observations"][0]["observation_id"] == "o1"
    assert data["verification_reports"][0]["status"] == "confirmed"
    assert data["falsification_reports"][0]["falsified"] is False
    assert data["scientific_theory_revisions"][0]["applied"] is False
    assert data["human_readable"]["predictions"]
    assert data["stage_cards"]
    assert data["raw_result"] is None


def test_scientific_analyze_full_release_chain_with_raw_result() -> None:
    response = client.post(
        "/scientific/analyze",
        json=release_payload(include_raw_result=True),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["raw_result"] is not None
    assert data["raw_result"]["plan"]["intent"] == "scientific_research"
    assert "persist" not in data["raw_result"]
    operators = {
        item["operator"]
        for item in data["operator_trace"]
    }
    assert "TheoryEvolutionOperator" in operators
    assert "PredictionOperator" in operators
    assert "VerificationOperator" in operators
    assert "FalsificationOperator" in operators
    assert "ScientificGapsOperator" in operators


def test_scientific_demo_release_compatibility() -> None:
    workbench = client.get("/scientific")
    assert workbench.status_code == 200
    assert "/scientific/analyze" in workbench.text

    page = client.get("/scientific-demo")
    assert page.status_code == 200
    assert "Version 0.9.6" in page.text

    response = client.post("/reasoning/scientific-demo", json={})

    assert response.status_code == 200
    data = response.json()
    assert {
        "summary",
        "human_readable",
        "stage_cards",
        "operator_trace",
        "raw_result",
        "scientific_predictions",
        "scientific_observations",
        "verification_reports",
        "falsification_reports",
        "scientific_gaps",
    } <= set(data)
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


def test_openapi_schema_is_available_for_release() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/scientific/health" in paths
    assert "/scientific/analyze" in paths
    assert "/reasoning/scientific-demo" in paths
