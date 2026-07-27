from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ConversationPipelineRequest:
    """
    Entrée normalisée du pipeline conversationnel.
    """

    question: str
    conversation_id: str | None = None
    include_evidence: bool = True

    def normalized_question(self) -> str:
        return " ".join(str(self.question or "").strip().split())


@dataclass(frozen=True)
class ConversationProcessingTrace:
    """
    Trace déterministe des transformations appliquées à une question.
    """

    original_question: str
    effective_question: str
    detected_intent: str
    is_follow_up: bool
    context: dict[str, Any]
    reference_resolution: dict[str, Any] | None
    question_rewrite: dict[str, Any] | None
    reasoning_plan: dict[str, Any] | None = None
    reasoning_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConversationPipelineResult:
    """
    Résultat complet retourné par ConversationPipeline.
    """

    conversation_id: str
    payload: dict[str, Any]
    processing: ConversationProcessingTrace

    def to_dict(self) -> dict[str, Any]:
        result = dict(self.payload)
        result["conversation_id"] = self.conversation_id
        result["conversation_processing"] = self.processing.to_dict()
        return result
