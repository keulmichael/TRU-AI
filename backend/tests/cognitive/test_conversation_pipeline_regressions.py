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
            "turn_count": 1,
        }


class FakeContextBuilder:
    def build(self, conversation: dict) -> FakeContext:
        return FakeContext(conversation["conversation_id"])


@dataclass
class FakeResolution:
    requires_context: bool = True

    def to_dict(self) -> dict:
        return {
            "requires_context": self.requires_context,
            "references": [{"type": "concept"}],
        }


class FakeReferenceResolver:
    def resolve(self, question: str, context: FakeContext) -> FakeResolution:
        return FakeResolution()


@dataclass
class FakeRewrite:
    original_question: str
    rewritten_question: str
    was_rewritten: bool
    warnings: tuple[str, ...]

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
        return FakeRewrite(
            original_question=question,
            rewritten_question="Explique le concept Delta.",
            was_rewritten=True,
            warnings=(
                "Référence résolue.",
                "référence résolue.",
                "Nouvel avertissement.",
            ),
        )


class FakeIntentDetector:
    def detect(self, question: str) -> str:
        if question == "Explique le concept Delta.":
            return "concept_explanation"

        return "conceptual_question"


@dataclass
class FakeResponse:
    request_id: str = "request-1"

    def to_dict(self, *, include_evidence: bool = True) -> dict:
        return {
            "request_id": self.request_id,
            "answer": {"summary": "Réponse"},
            "warnings": [
                "Avertissement existant.",
                "Référence résolue.",
            ],
            "evidence": ["preuve"] if include_evidence else [],
        }


class FakeCore:
    def __init__(self) -> None:
        self.questions = []

    def ask(self, question: str, *, include_evidence: bool = True):
        self.questions.append(question)
        return FakeResponse()


class FakeFollowUpBuilder:
    def is_follow_up_intent(self, intent: str) -> bool:
        return False


class FakeRepository:
    def __init__(self) -> None:
        self.conversation = {
            "conversation_id": "conversation-1",
            "turns": [{"question": "Question précédente"}],
        }
        self.saved_responses = []
        self.appended_turns = []

    def load_conversation(self, conversation_id: str):
        if conversation_id == "conversation-1":
            return self.conversation

        return None

    def create_conversation(self, conversation_id: str):
        self.conversation = {
            "conversation_id": conversation_id,
            "turns": [],
        }
        return self.conversation

    def get_last_conversation_turn(self, conversation_id: str):
        turns = self.conversation.get("turns", [])
        return turns[-1] if turns else None

    def save_response(self, response) -> None:
        self.saved_responses.append(response)

    def append_conversation_turn(self, **kwargs):
        self.appended_turns.append(kwargs)
        return kwargs


def test_pipeline_uses_rewritten_question_and_deduplicates_warnings() -> None:
    repository = FakeRepository()
    core = FakeCore()

    pipeline = ConversationPipeline(
        repository=repository,
        core=core,
        intent_detector=FakeIntentDetector(),
        context_builder=FakeContextBuilder(),
        reference_resolver=FakeReferenceResolver(),
        question_rewriter=FakeQuestionRewriter(),
        follow_up_builder=FakeFollowUpBuilder(),
    )

    result = pipeline.ask(
        ConversationPipelineRequest(
            question="Explique-le.",
            conversation_id="conversation-1",
        )
    ).to_dict()

    assert core.questions == ["Explique le concept Delta."]
    assert result["original_question"] == "Explique-le."
    assert result["rewritten_question"] == "Explique le concept Delta."
    assert result["was_rewritten"] is True
    assert result["intent"] == "concept_explanation"

    assert result["warnings"] == [
        "Avertissement existant.",
        "Référence résolue.",
        "Nouvel avertissement.",
    ]

    processing = result["conversation_processing"]
    assert processing["effective_question"] == "Explique le concept Delta."
    assert processing["question_rewrite"]["was_rewritten"] is True
    assert processing["reference_resolution"]["requires_context"] is True
