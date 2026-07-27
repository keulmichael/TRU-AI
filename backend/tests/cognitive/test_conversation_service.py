from __future__ import annotations

from dataclasses import dataclass

from tru_ai.cognitive.conversation.service import ConversationService


@dataclass
class FakePipelineResult:
    payload: dict

    def to_dict(self) -> dict:
        return dict(self.payload)


class FakePipeline:
    def __init__(self) -> None:
        self.requests = []

    def ask(self, request):
        self.requests.append(request)
        return FakePipelineResult(
            {
                "conversation_id": request.conversation_id or "generated-id",
                "question": request.question,
                "include_evidence": request.include_evidence,
            }
        )


class FakeRepository:
    def __init__(self) -> None:
        self.conversations = {
            "conversation-1": {
                "conversation_id": "conversation-1",
                "turns": [{"question": "Question précédente"}],
            }
        }
        self.requests = {
            "request-1": {
                "response": {
                    "request_id": "request-1",
                    "evidence": ["preuve-1"],
                },
                "trace": {
                    "coverage_score": 0.8,
                },
            }
        }

    def load_conversation(self, conversation_id: str):
        return self.conversations.get(conversation_id)

    def get_last_conversation_turn(self, conversation_id: str):
        conversation = self.load_conversation(conversation_id)

        if not conversation:
            return None

        turns = conversation.get("turns", [])
        return turns[-1] if turns else None

    def delete_conversation(self, conversation_id: str) -> bool:
        return self.conversations.pop(conversation_id, None) is not None

    def load_request(self, request_id: str):
        return self.requests.get(request_id)


def build_service() -> tuple[ConversationService, FakePipeline, FakeRepository]:
    repository = FakeRepository()
    pipeline = FakePipeline()
    service = ConversationService(
        repository=repository,
        pipeline=pipeline,
    )
    return service, pipeline, repository


def test_service_delegates_ask_to_pipeline() -> None:
    service, pipeline, _ = build_service()

    result = service.ask(
        question="Explique le Delta.",
        include_evidence=False,
        conversation_id="conversation-1",
    )

    assert len(pipeline.requests) == 1

    request = pipeline.requests[0]
    assert request.question == "Explique le Delta."
    assert request.include_evidence is False
    assert request.conversation_id == "conversation-1"

    assert result == {
        "conversation_id": "conversation-1",
        "question": "Explique le Delta.",
        "include_evidence": False,
    }


def test_service_returns_existing_conversation() -> None:
    service, _, _ = build_service()

    conversation = service.get_conversation("conversation-1")

    assert conversation is not None
    assert conversation["conversation_id"] == "conversation-1"


def test_service_returns_none_for_unknown_conversation() -> None:
    service, _, _ = build_service()

    assert service.get_conversation("missing") is None
    assert service.get_last_conversation_turn("missing") is None


def test_service_returns_last_conversation_turn() -> None:
    service, _, _ = build_service()

    turn = service.get_last_conversation_turn("conversation-1")

    assert turn == {
        "question": "Question précédente",
    }


def test_service_deletes_conversation() -> None:
    service, _, repository = build_service()

    assert service.delete_conversation("conversation-1") is True
    assert "conversation-1" not in repository.conversations
    assert service.delete_conversation("conversation-1") is False


def test_service_returns_request() -> None:
    service, _, _ = build_service()

    record = service.get_request("request-1")

    assert record is not None
    assert record["response"]["request_id"] == "request-1"


def test_service_builds_request_evidence_response() -> None:
    service, _, _ = build_service()

    result = service.get_request_evidence("request-1")

    assert result == {
        "request_id": "request-1",
        "evidence": ["preuve-1"],
        "trace": {
            "coverage_score": 0.8,
        },
    }


def test_service_normalizes_invalid_evidence_and_trace_shapes() -> None:
    service, _, repository = build_service()
    repository.requests["request-invalid"] = {
        "response": {
            "evidence": "preuve invalide",
        },
        "trace": "trace invalide",
    }

    result = service.get_request_evidence("request-invalid")

    assert result == {
        "request_id": "request-invalid",
        "evidence": [],
        "trace": {},
    }


def test_service_returns_none_for_unknown_request_evidence() -> None:
    service, _, _ = build_service()

    assert service.get_request_evidence("missing") is None
