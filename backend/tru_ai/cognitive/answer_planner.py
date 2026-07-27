from __future__ import annotations


class AnswerPlanner:
    def plan(self, intent: str) -> tuple[str, ...]:
        if intent == "applied_analysis":
            return (
                "rappeler_les_preuves_explicitement_disponibles",
                "identifier_les_concepts_applicables",
                "séparer_déductions_et_hypothèses",
                "signaler_les_limites_non_médicales",
                "justifier_la_confiance",
            )
        return (
            "identifier_le_concept",
            "sélectionner_définitions_et_passages",
            "relier_aux_concepts_voisins",
            "séparer_explicitement_déductions_hypothèses_inconnues",
            "justifier_la_confiance",
        )
