from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_string_sequence,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningClaim,
    ReasoningStage,
    ReasoningStep,
    TruthStatus,
)


class ClaimExtractionEngine:
    """
    Base commune aux moteurs qui classent des propositions.
    """

    stage: ReasoningStage
    context_keys: tuple[str, ...]
    truth_status: TruthStatus
    output_key: str

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        claims = self._extract_claims(state.relevant_context)
        state.claims.extend(claims)

        return {
            self.output_key: [
                claim.to_dict()
                for claim in claims
            ],
        }

    def _extract_claims(
        self,
        context: Mapping[str, Any],
    ) -> list[ReasoningClaim]:
        values: list[str] = []

        for key in self.context_keys:
            for value in normalize_string_sequence(
                context.get(key)
            ):
                if value not in values:
                    values.append(value)

        return [
            ReasoningClaim(
                text=value,
                status=self.truth_status,
            )
            for value in values
        ]


class ExplicitFactsEngine(ClaimExtractionEngine):
    """
    Extrait les éléments présentés comme explicites ou factuels.
    """

    stage = ReasoningStage.EXPLICIT_CLAIMS
    context_keys = ("explicit_claims", "facts")
    truth_status = TruthStatus.EXPLICIT
    output_key = "explicit_claims"


class DeductionEngine(ClaimExtractionEngine):
    """
    Classe les déductions déjà disponibles dans le contexte.
    """

    stage = ReasoningStage.DEDUCTIONS
    context_keys = ("deductions",)
    truth_status = TruthStatus.DEDUCTION
    output_key = "deductions"


class HypothesisEngine(ClaimExtractionEngine):
    """
    Classe les hypothèses déjà disponibles dans le contexte.
    """

    stage = ReasoningStage.HYPOTHESES
    context_keys = ("hypotheses",)
    truth_status = TruthStatus.HYPOTHESIS
    output_key = "hypotheses"
