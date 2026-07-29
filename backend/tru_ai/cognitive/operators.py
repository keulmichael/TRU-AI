from __future__ import annotations

import re

from tru_ai.cognitive.models import (
    CognitiveComparison,
    CognitiveEvidence,
    OperatorApplication,
    TruOperator,
    deterministic_id,
)


class DeltaOperatorEngine:
    def formalize(
        self,
        evidence: tuple[CognitiveEvidence, ...],
    ) -> TruOperator | None:
        delta_evidence = tuple(
            item
            for item in evidence
            if "delta" in item.text.lower()
            and item.semantic_validation_status in {"CONFIRMÉ", "PROBABLE"}
        )
        if not delta_evidence:
            return None
        definitions = tuple(
            item.text
            for item in delta_evidence
            if item.element_type in {"Définition", "Opérateur"}
            and any(
                marker in item.text.lower()
                for marker in (
                    "delta désigne",
                    "mesure de delta",
                    "delta mesure",
                    "écart entre",
                    "calcul de delta",
                )
            )
        )
        if not definitions:
            definitions = tuple(item.text for item in delta_evidence[:2])
        evidence_ids = tuple(item.evidence_id for item in delta_evidence)
        return TruOperator(
            operator_id=deterministic_id(
                "tru-operator",
                {
                    "name": "Delta",
                    "source_evidence": evidence_ids,
                },
            ),
            name="Delta",
            definitions=definitions[:5],
            inputs=(
                "état ou configuration actuelle",
                "possibilité, attente, prédiction ou configuration reconnue",
            ),
            preconditions=(
                "au moins deux états ou représentations comparables sont disponibles",
                "l'écart est soutenu par des preuves textuelles ou une comparaison explicite",
            ),
            transformation=(
                "Comparer deux états ou représentations pour rendre explicite l'écart pertinent."
            ),
            outputs=(
                "écart qualifié",
                "orientation possible de transformation",
            ),
            limitations=(
                "Delta ne doit pas être appliqué si un seul état est établi.",
                "Delta ne transforme pas une interprétation médicale en diagnostic.",
            ),
            source_evidence=evidence_ids,
            conceptual_version="v0.9.0-alpha",
        )

    def compare(
        self,
        *,
        question: str,
        evidence: tuple[CognitiveEvidence, ...],
    ) -> CognitiveComparison:
        states = self._explicit_states(question)
        provenance: list[str] = []
        dimensions = set()
        lower_question = question.lower()
        if not states:
            states.append(f"question formulée : {question}")
        if "burn-out" in lower_question or "burnout" in lower_question:
            dimensions.add("tension entre état vécu et possibilité reconnue")
        if evidence:
            provenance.extend(item.evidence_id for item in evidence)
            for item in evidence:
                if "écart" in item.text.lower() or "delta" in item.text.lower():
                    dimensions.add("écart")
                if "transformation" in item.text.lower():
                    dimensions.add("transformation")
                if "reconnaissance" in item.text.lower():
                    dimensions.add("reconnaissance")
        differences = []
        similarities = []
        if len(states) >= 2:
            similarities.append("la question peut être mise en rapport avec les concepts TRU sélectionnés")
            differences.append("le phénomène demandé n'est pas nécessairement affirmé directement par le traité")
        elif evidence:
            similarities.append("la mémoire contient des éléments pertinents pour le concept demandé")
        limitations = []
        delta_detected = None
        tru_meaning = None
        if len(states) >= 2 and (
            "delta" in lower_question
            or any(item for item in dimensions if item == "écart")
        ):
            delta_detected = "écart qualifié entre la demande formulée et les connaissances TRU sélectionnées"
            tru_meaning = "Delta sert ici à expliciter ce qui doit être comparé avant toute synthèse."
        else:
            limitations.append("comparaison insuffisante pour appliquer Delta comme opérateur complet")
        return CognitiveComparison(
            comparison_id=deterministic_id(
                "cognitive-comparison",
                {
                    "question": question,
                    "evidence": [item.evidence_id for item in evidence],
                    "states": states,
                },
            ),
            compared_states=tuple(states),
            provenance=tuple(provenance),
            dimensions=tuple(sorted(dimensions)),
            similarities=tuple(similarities),
            differences=tuple(differences),
            delta_detected=delta_detected,
            tru_meaning=tru_meaning,
            limitations=tuple(limitations),
        )

    @staticmethod
    def _explicit_states(question: str) -> list[str]:
        normalized = " ".join(question.strip().split())
        patterns = (
            r"état actuel est (?P<a>.+?) et l'état reconnu comme possible est (?P<b>.+?)(?:\.|$)",
            r"état actuel est (?P<a>.+?) et l'état possible est (?P<b>.+?)(?:\.|$)",
            r"X\s*=\s*(?P<a>.+?)[,;]\s*Y\s*=\s*(?P<b>.+?)(?:\.|$)",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match:
                return (
                    [
                        f"état actuel : {match.group('a').strip()}",
                        f"état reconnu possible : {match.group('b').strip()}",
                    ]
                )
        return []

    def apply(
        self,
        *,
        operator: TruOperator | None,
        comparison: CognitiveComparison,
    ) -> OperatorApplication:
        if operator is None:
            return OperatorApplication(
                application_id=deterministic_id(
                    "operator-application",
                    {
                        "operator": "Delta",
                        "comparison": comparison.comparison_id,
                        "applied": False,
                    },
                ),
                operator_id="delta",
                applied=False,
                refusal_reason="Delta n'est pas suffisamment formalisé par les preuves sélectionnées.",
                premise_evidence_ids=(),
                rule="delta_requires_formalized_operator",
                output=None,
                confidence=0.0,
            )
        if len(comparison.compared_states) < 2:
            return OperatorApplication(
                application_id=deterministic_id(
                    "operator-application",
                    {
                        "operator": operator.operator_id,
                        "comparison": comparison.comparison_id,
                        "applied": False,
                    },
                ),
                operator_id=operator.operator_id,
                applied=False,
                refusal_reason="Précondition non satisfaite : moins de deux états comparables sont établis.",
                premise_evidence_ids=operator.source_evidence,
                rule="delta_requires_two_comparable_states",
                output=None,
                confidence=0.0,
            )
        return OperatorApplication(
            application_id=deterministic_id(
                "operator-application",
                {
                    "operator": operator.operator_id,
                    "comparison": comparison.comparison_id,
                    "applied": True,
                },
            ),
            operator_id=operator.operator_id,
            applied=True,
            refusal_reason=None,
            premise_evidence_ids=operator.source_evidence,
            rule="delta_compares_current_state_with_recognized_possibility",
            output=comparison.delta_detected
            or "écart reconnu entre deux représentations comparées",
            confidence=0.62,
        )
