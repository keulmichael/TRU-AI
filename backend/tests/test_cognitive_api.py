from __future__ import annotations

from fastapi.testclient import TestClient

from tru_ai.api.main import app
from tru_ai.cognitive import api as cognitive_api


def test_cognitive_health_and_capabilities():
    cognitive_api.get_core.cache_clear()
    cognitive_api.get_repository.cache_clear()

    client = TestClient(app)

    health = client.get("/cognitive/health")
    capabilities = client.get("/cognitive/capabilities")

    assert health.status_code == 200
    assert capabilities.status_code == 200

    capabilities_data = capabilities.json()

    assert capabilities_data["llm_required"] is False
    assert any(
        capability["id"] == "conversation"
        for capability in capabilities_data["capabilities"]
    )


def test_cognitive_ask_and_evidence_roundtrip():
    cognitive_api.get_core.cache_clear()
    cognitive_api.get_repository.cache_clear()

    client = TestClient(app)

    response = client.post(
        "/cognitive/ask",
        json={
            "question": "Explique-moi Delta.",
            "include_evidence": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "request_id" in data
    assert "conversation_id" in data
    assert "classifications" in data

    stored = client.get(
        f"/cognitive/requests/{data['request_id']}"
    )

    evidence = client.get(
        f"/cognitive/requests/{data['request_id']}/evidence"
    )

    assert stored.status_code == 200
    assert evidence.status_code == 200


def test_root_serves_cognitive_interface():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "TRU-AI" in response.text
    assert "/cognitive/ask" in response.text


def test_scientific_demo_page_is_available():
    client = TestClient(app)

    response = client.get("/scientific-demo")

    assert response.status_code == 200
    assert "TRU-AI — Pipeline scientifique" in response.text
    assert "/reasoning/scientific-demo" in response.text


def test_cognitive_follow_up_reuses_previous_execution():
    cognitive_api.get_core.cache_clear()
    cognitive_api.get_repository.cache_clear()

    client = TestClient(app)

    first_response = client.post(
        "/cognitive/ask",
        json={
            "question": "Analyse le burn-out selon la TRU.",
            "include_evidence": True,
        },
    )

    assert first_response.status_code == 200

    first = first_response.json()

    assert "request_id" in first
    assert "conversation_id" in first

    conversation_id = first["conversation_id"]

    follow_up_response = client.post(
        "/cognitive/ask",
        json={
            "question": "Quelles hypothèses fais-tu ?",
            "include_evidence": True,
            "conversation_id": conversation_id,
        },
    )

    assert follow_up_response.status_code == 200

    follow_up = follow_up_response.json()

    assert follow_up["conversation_id"] == conversation_id
    assert follow_up["request_id"] == first["request_id"]
    assert follow_up["is_follow_up"] is True
    assert follow_up["follow_up_intent"] == "hypothesis_review"
    assert follow_up["answer"]["hypotheses"]


def test_cognitive_conversation_history():
    cognitive_api.get_core.cache_clear()
    cognitive_api.get_repository.cache_clear()

    client = TestClient(app)

    first_response = client.post(
        "/cognitive/ask",
        json={
            "question": "Explique-moi la reconnaissance.",
            "include_evidence": False,
        },
    )

    assert first_response.status_code == 200

    first = first_response.json()
    conversation_id = first["conversation_id"]

    follow_up_response = client.post(
        "/cognitive/ask",
        json={
            "question": "Quel est ton niveau de confiance ?",
            "include_evidence": False,
            "conversation_id": conversation_id,
        },
    )

    assert follow_up_response.status_code == 200

    conversation_response = client.get(
        f"/cognitive/conversations/{conversation_id}"
    )

    assert conversation_response.status_code == 200

    conversation = conversation_response.json()

    assert conversation["conversation_id"] == conversation_id
    assert conversation["turn_count"] == 2
    assert len(conversation["turns"]) == 2

    assert conversation["turns"][0]["is_follow_up"] is False
    assert conversation["turns"][1]["is_follow_up"] is True

    assert (
        conversation["turns"][1]["follow_up_intent"]
        == "confidence_review"
    )


def test_cognitive_conversation_last_turn():
    cognitive_api.get_core.cache_clear()
    cognitive_api.get_repository.cache_clear()

    client = TestClient(app)

    first_response = client.post(
        "/cognitive/ask",
        json={
            "question": "Analyse le burn-out selon la TRU.",
            "include_evidence": False,
        },
    )

    assert first_response.status_code == 200

    conversation_id = first_response.json()["conversation_id"]

    follow_up_question = "Quelles connaissances te manquent ?"

    follow_up_response = client.post(
        "/cognitive/ask",
        json={
            "question": follow_up_question,
            "include_evidence": False,
            "conversation_id": conversation_id,
        },
    )

    assert follow_up_response.status_code == 200

    last_turn_response = client.get(
        f"/cognitive/conversations/{conversation_id}/last"
    )

    assert last_turn_response.status_code == 200

    last_turn = last_turn_response.json()

    assert last_turn["question"] == follow_up_question
    assert last_turn["is_follow_up"] is True
    assert (
        last_turn["follow_up_intent"]
        == "missing_knowledge_review"
    )


def test_cognitive_conversation_can_be_deleted():
    cognitive_api.get_core.cache_clear()
    cognitive_api.get_repository.cache_clear()

    client = TestClient(app)

    first_response = client.post(
        "/cognitive/ask",
        json={
            "question": "Explique-moi Delta.",
            "include_evidence": False,
        },
    )

    assert first_response.status_code == 200

    conversation_id = first_response.json()["conversation_id"]

    deletion_response = client.delete(
        f"/cognitive/conversations/{conversation_id}"
    )

    assert deletion_response.status_code == 200
    assert deletion_response.json() == {
        "status": "deleted",
        "conversation_id": conversation_id,
    }

    missing_conversation_response = client.get(
        f"/cognitive/conversations/{conversation_id}"
    )

    assert missing_conversation_response.status_code == 404
