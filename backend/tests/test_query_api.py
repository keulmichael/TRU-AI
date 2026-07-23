from fastapi import FastAPI
from fastapi.testclient import TestClient

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.query import api
from tru_ai.query.graph_index import GraphIndex


def make_index() -> GraphIndex:
    nodes = (
        GraphNode(
            node_id="concept-conscience",
            label="Conscience",
            normalized_label="conscience",
            node_type="concept",
            concept_id="conscience",
            aliases={"conscience"},
        ),
        GraphNode(
            node_id="concept-realite",
            label="Réalité",
            normalized_label="realite",
            node_type="concept",
            concept_id="realite",
            aliases={"réalité"},
        ),
    )

    edge = GraphEdge(
        edge_id="edge-001",
        subject_id="concept-conscience",
        predicate="observer",
        object_id="concept-realite",
        occurrence_count=1,
        confidence_sum=0.92,
        confidence_max=0.92,
    )

    return GraphIndex(
        KnowledgeGraph(
            nodes=nodes,
            edges=(edge,),
        )
    )


def create_client(
    monkeypatch,
) -> TestClient:
    index = make_index()

    monkeypatch.setattr(
        api,
        "get_index",
        lambda: index,
    )

    app = FastAPI()
    app.include_router(api.router)

    return TestClient(app)


def test_query_health(
    monkeypatch,
) -> None:
    client = create_client(
        monkeypatch
    )

    response = client.get(
        "/query/health"
    )

    assert response.status_code == 200
    assert response.json()[
        "node_count"
    ] == 2


def test_find_node_endpoint(
    monkeypatch,
) -> None:
    client = create_client(
        monkeypatch
    )

    response = client.get(
        "/query/node/conscience"
    )

    assert response.status_code == 200

    assert response.json()[
        "node_id"
    ] == "concept-conscience"


def test_neighbors_endpoint(
    monkeypatch,
) -> None:
    client = create_client(
        monkeypatch
    )

    response = client.get(
        "/query/neighbors/conscience"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_path_endpoint(
    monkeypatch,
) -> None:
    client = create_client(
        monkeypatch
    )

    response = client.get(
        "/query/path",
        params={
            "from": "conscience",
            "to": "réalité",
            "directed": True,
        },
    )

    assert response.status_code == 200
    assert response.json()[
        "found"
    ] is True