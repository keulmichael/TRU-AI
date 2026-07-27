from __future__ import annotations

from tru_ai.cognitive.models import CognitiveAnswer, OperatorApplication


class SelfEvaluator:
    def breakdown(
        self,
        answer: CognitiveAnswer,
        *,
        production_source_count: int = 0,
        contradictions: tuple[str, ...] = (),
        operator_applications: tuple[OperatorApplication, ...] = (),
    ) -> dict[str, float]:
        evidence_quality = self._evidence_quality(answer)
        source_coverage = 0.95 if production_source_count else 0.35
        explicit_count = len(answer.explicit_claims)
        deduction_count = len(answer.deductions)
        hypothesis_count = len(answer.hypotheses)
        unknown_count = len(answer.unknowns)
        applied = [item for item in operator_applications if item.applied]
        refused = [item for item in operator_applications if not item.applied]
        reasoning_validity = 0.4
        if explicit_count:
            reasoning_validity += 0.25
        if deduction_count:
            reasoning_validity += min(0.25, deduction_count * 0.12)
        if unknown_count:
            reasoning_validity -= min(0.25, unknown_count * 0.12)
        operator_validity = 0.65
        if applied:
            operator_validity = min(
                application.confidence for application in applied
            )
        elif refused:
            operator_validity = 0.82
        hypothesis_penalty = min(0.35, hypothesis_count * 0.12)
        contradiction_penalty = min(0.4, len(contradictions) * 0.2)
        unknown_penalty = min(0.35, unknown_count * 0.18)
        final = (
            source_coverage * 0.18
            + evidence_quality * 0.32
            + max(0.0, min(1.0, reasoning_validity)) * 0.24
            + operator_validity * 0.14
            - hypothesis_penalty
            - contradiction_penalty
            - unknown_penalty
        )
        return {
            "source_coverage": source_coverage,
            "evidence_quality": evidence_quality,
            "reasoning_validity": max(0.0, min(1.0, reasoning_validity)),
            "operator_validity": operator_validity,
            "hypothesis_penalty": hypothesis_penalty,
            "contradiction_penalty": contradiction_penalty,
            "unknown_penalty": unknown_penalty,
            "final_confidence": max(0.0, min(1.0, final)),
        }

    def evaluate(
        self,
        answer: CognitiveAnswer,
        *,
        production_source_count: int = 0,
        contradictions: tuple[str, ...] = (),
        operator_applications: tuple[OperatorApplication, ...] = (),
    ) -> tuple[float, str]:
        unknown_count = len(answer.unknowns)
        if unknown_count and not len(answer.explicit_claims):
            return 0.0, "Aucune preuve explicite disponible."
        breakdown = self.breakdown(
            answer,
            production_source_count=production_source_count,
            contradictions=contradictions,
            operator_applications=operator_applications,
        )
        score = breakdown["final_confidence"]
        return (
            round(score, 6),
            (
                "Confiance décomposée : "
                f"couverture={breakdown['source_coverage']:.2f}, "
                f"preuves={breakdown['evidence_quality']:.2f}, "
                f"raisonnement={breakdown['reasoning_validity']:.2f}, "
                f"opérateur={breakdown['operator_validity']:.2f}, "
                f"pénalité_hypothèses={breakdown['hypothesis_penalty']:.2f}, "
                f"pénalité_contradictions={breakdown['contradiction_penalty']:.2f}, "
                f"pénalité_inconnues={breakdown['unknown_penalty']:.2f}."
            ),
        )

    @staticmethod
    def _evidence_quality(answer: CognitiveAnswer) -> float:
        claims = answer.explicit_claims
        if not claims:
            return 0.0
        return min(1.0, sum(claim.confidence for claim in claims) / len(claims))
