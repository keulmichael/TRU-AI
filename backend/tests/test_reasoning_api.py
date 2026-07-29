from fastapi import FastAPI
from fastapi.testclient import TestClient

from tru_ai.reasoning import api
from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
)


def make_store() -> api.ReasoningStore:
    proof = ProofTreeNode(
        node_id="proof-tree-1",
        edge_id="edge-1",
        edge_key=("node-a", "is_a", "node-b"),
        node_type="inferred_fact",
        rule_id="rule-1",
        confidence=0.9,
        depth=1,
    )
    explanation = ReasoningExplanation(
        explanation_id="explanation-1",
        inferred_edge_id="edge-1",
        conclusion_edge_key=(
            "node-a",
            "is_a",
            "node-b",
        ),
        rule_ids=("rule-1",),
        steps=(),
        proof_tree_id="proof-tree-1",
        maximum_depth=1,
        confidence=0.9,
        deterministic_text="text",
    )

    return api.ReasoningStore(
        explanations_by_edge_id={
            "edge-1": explanation
        },
        proof_trees_by_edge_id={
            "edge-1": proof
        },
    )


def create_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(
        api,
        "get_store",
        lambda: make_store(),
    )
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app)


def test_reasoning_health(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.get(
        "/reasoning/health"
    )

    assert response.status_code == 200
    assert response.json()[
        "explanation_count"
    ] == 1
    assert response.json()["loaded"] is True


def test_reasoning_explain_200(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.get(
        "/reasoning/explain/edge-1"
    )

    assert response.status_code == 200
    assert response.json()[
        "inferred_edge_id"
    ] == "edge-1"


def test_reasoning_proof_200(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.get(
        "/reasoning/proof/edge-1"
    )

    assert response.status_code == 200
    assert response.json()["edge_id"] == "edge-1"


def test_reasoning_404(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.get(
        "/reasoning/explain/missing"
    )

    assert response.status_code == 404


def test_reasoning_reload(monkeypatch) -> None:
    class CallableStore:
        def __call__(self):
            return make_store()

        def cache_clear(self):
            self.cleared = True

    callable_store = CallableStore()
    monkeypatch.setattr(
        api,
        "get_store",
        callable_store,
    )
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    response = client.post(
        "/reasoning/reload"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reloaded"
    assert callable_store.cleared is True


def test_scientific_demo_runs_full_pipeline(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.post(
        "/reasoning/scientific-demo",
        json={
            "observation": (
                "La reconnaissance répétée ne stabilise pas cette relation."
            ),
            "claims": [
                "La reconnaissance répétée stabilise une relation.",
                "Une relation stabilisée rend les prédictions plus robustes.",
            ],
            "prediction_rule": {
                "id": "rule-stability",
                "statement": (
                    "La répétition de la reconnaissance augmente la stabilité."
                ),
                "confidence": 0.85,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    trace = {
        item["operator"]
        for item in data["operator_trace"]
    }

    assert "TheoryEvolutionOperator" in trace
    assert "PredictionOperator" in trace
    assert "VerificationOperator" in trace
    assert "FalsificationOperator" in trace
    assert "human_readable" in data
    assert "raw_result" in data
    assert data["summary"]["falsified"] is True
    assert data["summary"]["revision_required"] is True
    assert data["summary"]["verification_status"] == "contradicted"
    assert "contredite" in data["human_readable"]["conclusion"]
    assert "Falsifié : True" in data["human_readable"]["falsification_explanation"]


def test_scientific_demo_human_readable_reflexive_view(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.post(
        "/reasoning/scientific-demo",
        json={},
    )

    assert response.status_code == 200
    view = response.json()["human_readable"]["reflexive_view"]

    assert set(view) == {
        "observed",
        "recognized",
        "predicted",
        "confirmed_or_refuted_by",
        "learning",
    }
    assert view["observed"]
    assert view["predicted"]


def test_scientific_demo_human_readable_does_not_invent_missing_data() -> None:
    human = api._build_human_readable({})

    assert "Non déterminé par cette exécution." in human["conclusion"]
    assert all(
        value == "Non déterminé par cette exécution."
        for value in human["reflexive_view"].values()
    )


def test_scientific_demo_confirmatory_case_is_supported(monkeypatch) -> None:
    client = create_client(monkeypatch)

    response = client.post(
        "/reasoning/scientific-demo",
        json={
            "observation": (
                "La reconnaissance répétée stabilise cette relation."
            ),
            "claims": [
                "La reconnaissance répétée stabilise une relation.",
                "Une relation stabilisée rend les prédictions plus robustes.",
            ],
            "prediction_rule": {
                "id": "rule-stability",
                "statement": (
                    "La répétition de la reconnaissance augmente la stabilité."
                ),
                "confidence": 0.85,
            },
            "compatibility_score": 0.9,
            "matches_falsification_condition": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["summary"]["verification_status"] == "confirmed"
    assert data["summary"]["falsified"] is False
    assert data["summary"]["final_action"] == "retain"
    assert "confirmée" in data["human_readable"]["conclusion"]
