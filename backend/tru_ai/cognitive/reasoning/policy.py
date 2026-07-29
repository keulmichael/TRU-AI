from __future__ import annotations

from dataclasses import dataclass

from tru_ai.cognitive.reasoning.models import ReasoningStage


@dataclass(frozen=True)
class ReasoningPolicy:
    """
    Politique de construction des plans de raisonnement.

    Elle centralise les règles d'activation des étapes afin d'éviter de
    disperser ces décisions dans le pipeline conversationnel ou dans l'API.
    """

    version: str = "tru-reasoning-v1"

    def stages_for_intent(
        self,
        intent: str,
    ) -> tuple[ReasoningStage, ...]:
        normalized_intent = str(intent or "").strip().casefold()


        if normalized_intent in {
            "scientific_research",
            "theory_analysis",
            "theory_comparison",
            "theory_evolution",
        }:
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.DEDUCTIONS,
                ReasoningStage.HYPOTHESES,
                ReasoningStage.RECOGNITION,
                ReasoningStage.DELTA,
                ReasoningStage.REFLEXIVITY,
                ReasoningStage.RECOGNITION_MEANING,
                ReasoningStage.THEORY_CONSTRUCTION,
                ReasoningStage.THEORY_COMPARISON,
                ReasoningStage.THEORY_EVOLUTION,
                ReasoningStage.PREDICTION,
                ReasoningStage.VERIFICATION,
                ReasoningStage.FALSIFICATION,
                ReasoningStage.SCIENTIFIC_GAPS,
                ReasoningStage.CONTRADICTIONS,
                ReasoningStage.MISSING_KNOWLEDGE,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "supporting_arguments":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.DEDUCTIONS,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "hypothesis_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.HYPOTHESES,
                ReasoningStage.MISSING_KNOWLEDGE,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "confidence_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.DEDUCTIONS,
                ReasoningStage.HYPOTHESES,
                ReasoningStage.MISSING_KNOWLEDGE,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "recognition_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.RECOGNITION,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "delta_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.RECOGNITION,
                ReasoningStage.DELTA,
                ReasoningStage.REFLEXIVITY,
                ReasoningStage.RECOGNITION_MEANING,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "reflexivity_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.RECOGNITION,
                ReasoningStage.DELTA,
                ReasoningStage.REFLEXIVITY,
                ReasoningStage.RECOGNITION_MEANING,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "recognition_meaning_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.RECOGNITION,
                ReasoningStage.DELTA,
                ReasoningStage.REFLEXIVITY,
                ReasoningStage.RECOGNITION_MEANING,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "contradiction_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.EXPLICIT_CLAIMS,
                ReasoningStage.DEDUCTIONS,
                ReasoningStage.HYPOTHESES,
                ReasoningStage.RECOGNITION,
                ReasoningStage.DELTA,
                ReasoningStage.REFLEXIVITY,
                ReasoningStage.RECOGNITION_MEANING,
                ReasoningStage.CONTRADICTIONS,
                ReasoningStage.SYNTHESIS,
            )

        if normalized_intent == "missing_knowledge_review":
            return (
                ReasoningStage.OBSERVATION,
                ReasoningStage.CONTEXT,
                ReasoningStage.MISSING_KNOWLEDGE,
                ReasoningStage.SYNTHESIS,
            )

        return (
            ReasoningStage.OBSERVATION,
            ReasoningStage.CONTEXT,
            ReasoningStage.EXPLICIT_CLAIMS,
            ReasoningStage.DEDUCTIONS,
            ReasoningStage.HYPOTHESES,
            ReasoningStage.RECOGNITION,
            ReasoningStage.DELTA,
            ReasoningStage.REFLEXIVITY,
            ReasoningStage.RECOGNITION_MEANING,
            ReasoningStage.THEORY_CONSTRUCTION,
            ReasoningStage.THEORY_COMPARISON,
            ReasoningStage.THEORY_EVOLUTION,
            ReasoningStage.PREDICTION,
            ReasoningStage.VERIFICATION,
            ReasoningStage.FALSIFICATION,
            ReasoningStage.SCIENTIFIC_GAPS,
            ReasoningStage.CONTRADICTIONS,
            ReasoningStage.MISSING_KNOWLEDGE,
            ReasoningStage.SYNTHESIS,
        )
