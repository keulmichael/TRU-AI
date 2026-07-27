from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
)


class ContextEngine:
    """
    Expose le contexte conversationnel pertinent au raisonnement.

    Cette version conserve le contexte complet. Une politique de sélection
    sémantique pourra être ajoutée ultérieurement.
    """

    stage = ReasoningStage.CONTEXT

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        relevant_context = dict(state.conversation_context)
        state.relevant_context = relevant_context

        return {
            "relevant_context": relevant_context,
        }
