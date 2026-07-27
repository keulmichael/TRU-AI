from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_string_sequence,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
)


class MissingKnowledgeEngine:
    """
    Extrait les connaissances déclarées manquantes.
    """

    stage = ReasoningStage.MISSING_KNOWLEDGE

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        missing_knowledge = normalize_string_sequence(
            state.relevant_context.get("missing_knowledge")
        )
        state.missing_knowledge.extend(missing_knowledge)

        return {
            "missing_knowledge": missing_knowledge,
        }
