from __future__ import annotations


class ReasoningOrchestrator:
    """
    Point d'intégration déterministe vers les moteurs d'inférence
    et de raisonnement existants.

    La version alpha n'invente pas de preuve si les moteurs internes
    n'en fournissent pas. Elle expose donc une orchestration vide mais
    explicite, testable et extensible.
    """

    def select_inferences(self, concept_ids: tuple[str, ...]) -> tuple[str, ...]:
        return ()

    def select_reasoning_proofs(self, evidence_ids: tuple[str, ...]) -> tuple[str, ...]:
        return ()
