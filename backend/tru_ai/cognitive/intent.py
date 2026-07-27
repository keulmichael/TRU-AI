from __future__ import annotations


class IntentDetector:
    """
    Détecte l'intention principale de la question.

    Les intentions de suivi sont utilisées lorsqu'une conversation est déjà
    ouverte afin de réutiliser la dernière réponse cognitive.
    """

    def detect(self, question: str) -> str:
        normalized = question.lower().strip()

        # ------------------------------------------------------------
        # Analyses appliquées
        # ------------------------------------------------------------

        if "burn-out" in normalized or "burnout" in normalized:
            return "applied_analysis"

        # ------------------------------------------------------------
        # Questions de suivi : preuves
        # ------------------------------------------------------------

        if any(
            keyword in normalized
            for keyword in (
                "preuve",
                "preuves",
                "argument",
                "arguments",
                "soutiennent",
                "sur quoi te bases",
                "sur quoi tu te bases",
                "quelles sont tes preuves",
                "pourquoi dis-tu cela",
            )
        ):
            return "supporting_arguments"

        # ------------------------------------------------------------
        # Questions de suivi : hypothèses
        # ------------------------------------------------------------

        if any(
            keyword in normalized
            for keyword in (
                "hypoth",
                "hypothèse",
                "hypothèses",
            )
        ):
            return "hypothesis_review"

        # ------------------------------------------------------------
        # Questions de suivi : confiance
        # ------------------------------------------------------------

        if any(
            keyword in normalized
            for keyword in (
                "confiance",
                "fiabilité",
                "fiable",
                "certain",
                "certitude",
            )
        ):
            return "confidence_review"

        # ------------------------------------------------------------
        # Questions de suivi : connaissances manquantes
        # ------------------------------------------------------------

        if (
            "connaissance" in normalized
            or "connaissances" in normalized
            or "information" in normalized
            or "informations" in normalized
        ) and (
            "manque" in normalized
            or "manquent" in normalized
            or "insuffisant" in normalized
        ):
            return "missing_knowledge_review"

        # ------------------------------------------------------------
        # Questions de suivi : contradictions
        # ------------------------------------------------------------

        if any(
            keyword in normalized
            for keyword in (
                "contradiction",
                "contradictions",
                "contredi",
                "incohérence",
                "incohérences",
            )
        ):
            return "contradiction_review"

        # ------------------------------------------------------------
        # Explication d'un concept
        # ------------------------------------------------------------

        if any(
            marker in normalized
            for marker in (
                "explique",
                "qu'est-ce",
                "que signifie",
                "définis",
                "definis",
                "définition",
                "c'est quoi",
            )
        ):
            return "concept_explanation"

        # ------------------------------------------------------------
        # Cas général
        # ------------------------------------------------------------

        return "conceptual_question"