from __future__ import annotations

from dataclasses import dataclass

from tru_ai.cognitive.conversation.models import (
    ConversationPipelineRequest,
)
from tru_ai.cognitive.conversation.pipeline import ConversationPipeline


@dataclass
class FakeContext:
    conversation_id: str

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "turn_count": 0,
        }


class FakeContextBuilder:
    def build(self, conversation: dict) -> FakeContext:
        return FakeContext(conversation["conversation_id"])


@dataclass
class FakeResolution:
    def to_dict(self) -> dict:
        return {
            "requires_context": False,
            "references": [],
        }


class FakeReferenceResolver:
    def resolve(self, question: str, context: FakeContext) -> FakeResolution:
        return FakeResolution()


@dataclass
class FakeRewrite:
    original_question: str
    rewritten_question: str
    was_rewritten: bool = False
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "original_question": self.original_question,
            "rewritten_question": self.rewritten_question,
            "was_rewritten": self.was_rewritten,
            "warnings": list(self.warnings),
        }


class FakeQuestionRewriter:
    def rewrite(
        self,
        *,
        question: str,
        context: FakeContext,
        resolution: FakeResolution,
    ) -> FakeRewrite:
        return FakeRewrite(question, question)


class FakeIntentDetector:
    def detect(self, question: str) -> str:
        if "hypothèses" in question.casefold():
            return "hypothesis_review"

        return "conceptual_question"


@dataclass
class FakeResponse:
    request_id: str = "request-1"

    def to_dict(self, *, include_evidence: bool = True) -> dict:
        return {
            "request_id": self.request_id,
            "answer": {"summary": "Réponse"},
            "warnings": [],
            "evidence": ["preuve"] if include_evidence else [],
        }


class FakeCore:
    def __init__(self) -> None:
        self.questions: list[str] = []

    def ask(self, question: str, *, include_evidence: bool = True):
        self.questions.append(question)
        return FakeResponse()


class FakeFollowUpBuilder:
    def is_follow_up_intent(self, intent: str) -> bool:
        return intent == "hypothesis_review"

    def build(self, **kwargs) -> dict:
        return {
            "request_id": "request-1",
            "conversation_id": kwargs["conversation_id"],
            "question": kwargs["question"],
            "intent": kwargs["intent"],
            "is_follow_up": True,
            "answer": {"hypotheses": ["H1"]},
        }


class FakeRepository:
    def __init__(self, *, with_previous_turn: bool = False) -> None:
        self.conversations: dict[str, dict] = {}
        self.saved_responses: list[FakeResponse] = []
        self.appended_turns: list[dict] = []
        self.with_previous_turn = with_previous_turn

    def conversation_exists(self, conversation_id: str) -> bool:
        return conversation_id in self.conversations

    def create_conversation(self, conversation_id: str) -> dict:
        conversation = {
            "conversation_id": conversation_id,
            "turns": [],
        }
        self.conversations[conversation_id] = conversation
        return conversation

    def load_conversation(self, conversation_id: str) -> dict | None:
        return self.conversations.get(conversation_id)

    def get_last_conversation_turn(self, conversation_id: str):
        if not self.with_previous_turn:
            return None

        return {
            "question": "Question précédente",
            "response": {
                "request_id": "request-1",
                "answer": {
                    "hypotheses": ["H1"],
                },
            },
        }

    def save_response(self, response: FakeResponse) -> None:
        self.saved_responses.append(response)

    def append_conversation_turn(self, **kwargs) -> dict:
        self.appended_turns.append(kwargs)
        return kwargs


def build_pipeline(
    repository: FakeRepository,
    core: FakeCore,
) -> ConversationPipeline:
    return ConversationPipeline(
        repository=repository,
        core=core,
        intent_detector=FakeIntentDetector(),
        context_builder=FakeContextBuilder(),
        reference_resolver=FakeReferenceResolver(),
        question_rewriter=FakeQuestionRewriter(),
        follow_up_builder=FakeFollowUpBuilder(),
    )


def test_pipeline_executes_core_and_persists_response() -> None:
    repository = FakeRepository()
    core = FakeCore()
    pipeline = build_pipeline(repository, core)

    result = pipeline.ask(
        ConversationPipelineRequest(
            question="  Explique le Delta.  ",
            conversation_id="conversation-1",
            include_evidence=False,
        )
    ).to_dict()

    assert core.questions == ["Explique le Delta."]
    assert len(repository.saved_responses) == 1
    assert len(repository.appended_turns) == 1
    assert result["conversation_id"] == "conversation-1"
    assert result["is_follow_up"] is False
    assert result["evidence"] == []
    assert result["conversation_processing"]["effective_question"] == (
        "Explique le Delta."
    )


def test_pipeline_creates_identifier_when_missing() -> None:
    repository = FakeRepository()
    core = FakeCore()
    pipeline = build_pipeline(repository, core)

    result = pipeline.ask(
        ConversationPipelineRequest(
            question="Explique le Delta.",
        )
    ).to_dict()

    assert result["conversation_id"]
    assert repository.conversation_exists(
        result["conversation_id"]
    )


def test_specialized_follow_up_does_not_execute_core() -> None:
    repository = FakeRepository(with_previous_turn=True)
    repository.create_conversation("conversation-1")
    core = FakeCore()
    pipeline = build_pipeline(repository, core)

    result = pipeline.ask(
        ConversationPipelineRequest(
            question="Quelles sont les hypothèses ?",
            conversation_id="conversation-1",
        )
    ).to_dict()

    assert core.questions == []
    assert repository.saved_responses == []
    assert result["is_follow_up"] is True
    assert result["answer"]["hypotheses"] == ["H1"]
    assert result["conversation_processing"]["is_follow_up"] is True
