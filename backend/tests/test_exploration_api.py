from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.test_exploration_indexes import make_graph
from tru_ai.exploration import api
from tru_ai.exploration.indexes import ExplorationIndexes


def create_client(monkeypatch) -> TestClient:
    indexes = ExplorationIndexes(make_graph())

    class Store:
        def __call__(self):
            return indexes

        def cache_clear(self):
            self.cleared = True

    store = Store()
    monkeypatch.setattr(api, "get_indexes", store)
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app)


def test_exploration_health(monkeypatch) -> None:
    response = create_client(monkeypatch).get(
        "/exploration/health"
    )

    assert response.status_code == 200
    assert response.json()["node_count"] == 2


def test_exploration_nodes(monkeypatch) -> None:
    response = create_client(monkeypatch).get(
        "/exploration/nodes",
        params={"search": "Alpha"},
    )

    assert response.status_code == 200
    assert response.json()["nodes"][0]["node_id"] == "node-a"


def test_exploration_node_404(monkeypatch) -> None:
    response = create_client(monkeypatch).get(
        "/exploration/nodes/missing"
    )

    assert response.status_code == 404


def test_exploration_neighborhood(monkeypatch) -> None:
    response = create_client(monkeypatch).get(
        "/exploration/neighborhood/node-a",
        params={"depth": 1},
    )

    assert response.status_code == 200
    assert "node-b" in response.json()["node_ids"]


def test_exploration_paths(monkeypatch) -> None:
    response = create_client(monkeypatch).get(
        "/exploration/paths",
        params={
            "start_node_id": "node-a",
            "end_node_id": "node-b",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_exploration_pattern(monkeypatch) -> None:
    response = create_client(monkeypatch).post(
        "/exploration/pattern",
        json={
            "variables": ["?x", "?y"],
            "constraints": [
                {
                    "subject": "?x",
                    "predicate": "contains",
                    "object": "?y",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_exploration_pattern_422(monkeypatch) -> None:
    response = create_client(monkeypatch).post(
        "/exploration/pattern",
        json={"variables": ["?x"], "constraints": []},
    )

    assert response.status_code == 422


def test_exploration_reload(monkeypatch) -> None:
    response = create_client(monkeypatch).post(
        "/exploration/reload"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reloaded"
