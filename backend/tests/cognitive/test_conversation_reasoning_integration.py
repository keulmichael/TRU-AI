from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tru_ai.cognitive.conversation.models import (
    ConversationPipelineRequest,
    ConversationProcessingTrace,
)
from tru_ai.cognitive.conversation.pipeline import ConversationPipeline
from tru_ai.cognitive.reasoning.models import (
    ReasoningPlan,
    ReasoningResult,
    ReasoningStage,
    ReasoningStep,
)


@dataclass
class FakeContext:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class FakeContextBuilder:
    def build(self, conversation: dict[str, Any]) -> FakeContext:
        return FakeContext(
            {
                "explicit_claims": ["Le Delta représente un écart."],
                "deductions": [
                    "Un écart suppose deux états comparables.",
                ],
            }
        )


class FakeReferenceResolution:
    def to_dict(self) -> dict[str, Any]:
        return {
            "references": [],
        }


class FakeReferenceResolver:
    def resolve(self, question: str, context: FakeContext):
        return FakeReferenceResolution()


class FakeRewrite:
    rewritten_question = "Explique le Delta."
    was_rewritten = True
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rewritten_question": self.rewritten_question,
            "was_rewritten": self.was_rewritten,
        }


class FakeQuestionRewriter:
    def rewrite(self, *, question, context, resolution):
        return FakeRewrite()


class FakeIntentDetector:
    def detect(self, question: str) -> str:
        return "concept_explanation"


class FakeFollowUpBuilder:
    def is_follow_up_intent(self, intent: str) -> bool:
        return False


class FakeResponse:
    def to_dict(self, *, include_evidence: bool) -> dict[str, Any]:
        return {
            "answer": "Réponse cognitive.",
        }


class FakeCore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def ask(
        self,
        question: str,
        *,
        include_evidence: bool = True,
    ) -> FakeResponse:
        self.calls.append((question, include_evidence))
        return FakeResponse()


class FakeRepository:
    def __init__(self) -> None:
        self.saved_responses: list[Any] = []
        self.turns: list[dict[str, Any]] = []

    def load_conversation(self, conversation_id: str):
        return {
            "conversation_id": conversation_id,
            "turns": [],
        }

    def create_conversation(self, conversation_id: str):
        return {
            "conversation_id": conversation_id,
            "turns": [],
        }

    def get_last_conversation_turn(self, conversation_id: str):
        return None

    def save_response(self, response: Any) -> None:
        self.saved_responses.append(response)

    def append_conversation_turn(self, **kwargs: Any) -> None:
        self.turns.append(kwargs)


class SpyReasoningPlanner:
    def __init__(self) -> None:
        self.requests = []

    def plan(self, request):
        self.requests.append(request)
        return ReasoningPlan(
            question=request.question,
            intent=request.intent,
            steps=(
                ReasoningStep(
                    position=1,
                    stage=ReasoningStage.OBSERVATION,
                    objective="Observer.",
                ),
            ),
        )


class SpyReasoningExecutor:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, plan, *, conversation_context=None):
        self.calls.append((plan, conversation_context))
        return ReasoningResult(
            plan=plan,
            synthesis="Raisonnement exécuté.",
        )


def test_pipeline_integrates_reasoning_before_core() -> None:
    repository = FakeRepository()
    core = FakeCore()
    planner = SpyReasoningPlanner()
    executor = SpyReasoningExecutor()

    pipeline = ConversationPipeline(
        repository=repository,
        core=core,
        intent_detector=FakeIntentDetector(),
        context_builder=FakeContextBuilder(),
        reference_resolver=FakeReferenceResolver(),
        question_rewriter=FakeQuestionRewriter(),
        follow_up_builder=FakeFollowUpBuilder(),
        reasoning_planner=planner,
        reasoning_executor=executor,
    )

    result = pipeline.ask(
        ConversationPipelineRequest(
            question="Explique-le.",
            conversation_id="conversation-1",
            include_evidence=False,
        )
    )

    assert len(planner.requests) == 1
    assert planner.requests[0].question == "Explique le Delta."
    assert planner.requests[0].intent == "concept_explanation"
    assert planner.requests[0].conversation_context == {
        "explicit_claims": ["Le Delta représente un écart."],
        "deductions": [
            "Un écart suppose deux états comparables.",
        ],
    }

    assert len(executor.calls) == 1
    assert executor.calls[0][1] == planner.requests[0].conversation_context

    assert core.calls == [
        ("Explique le Delta.", False),
    ]

    assert result.payload["reasoning_plan"]["question"] == (
        "Explique le Delta."
    )
    assert result.payload["reasoning_result"]["synthesis"] == (
        "Raisonnement exécuté."
    )
    assert result.processing.reasoning_plan is not None
    assert result.processing.reasoning_result is not None


def test_processing_trace_remains_backward_compatible() -> None:
    trace = ConversationProcessingTrace(
        original_question="Question",
        effective_question="Question",
        detected_intent="concept_explanation",
        is_follow_up=False,
        context={},
        reference_resolution=None,
        question_rewrite=None,
    )

    payload = trace.to_dict()

    assert payload["reasoning_plan"] is None
    assert payload["reasoning_result"] is None
