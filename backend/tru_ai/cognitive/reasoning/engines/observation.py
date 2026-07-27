from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_text,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
)


class ObservationEngine:
    """
    Normalise le problème formulé sans ajouter d'interprétation.
    """

    stage = ReasoningStage.OBSERVATION

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        normalized_problem = normalize_text(state.question)
        state.normalized_problem = normalized_problem

        return {
            "normalized_problem": normalized_problem,
        }
