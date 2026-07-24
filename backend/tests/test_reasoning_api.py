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
