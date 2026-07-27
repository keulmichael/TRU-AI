from __future__ import annotations

from typing import Any, Mapping


FOLLOW_UP_INTENTS = frozenset(
    {
        "supporting_arguments",
        "hypothesis_review",
        "confidence_review",
        "contradiction_review",
        "missing_knowledge_review",
    }
)


class FollowUpResponseBuilder:
    """
    Construit une réponse de suivi à partir d'une réponse cognitive antérieure.

    Ce composant ne relance pas le CognitiveCore et ne produit aucun nouveau
    raisonnement. Il sélectionne uniquement les informations déjà présentes
    dans la réponse précédente en fonction de l'intention détectée.
    """

    def is_follow_up_intent(self, intent: str) -> bool:
        return intent in FOLLOW_UP_INTENTS

    def build(
        self,
        *,
        conversation_id: str,
        question: str,
        intent: str,
        previous_turn: Mapping[str, Any],
        include_evidence: bool,
    ) -> dict[str, Any]:
        normalized_question = self._normalize_required_text(
            question,
            field_name="question",
        )
        normalized_intent = self._normalize_required_text(
            intent,
            field_name="intent",
        )
        normalized_conversation_id = self._normalize_required_text(
            conversation_id,
            field_name="conversation_id",
        )

        if not self.is_follow_up_intent(normalized_intent):
            raise ValueError(
                f"Intention de suivi non prise en charge : {normalized_intent}."
            )

        previous_response = self._mapping(previous_turn.get("response"))
        previous_request_id = self._optional_text(
            previous_response.get("request_id")
        )
        previous_question = self._optional_text(previous_turn.get("question"))

        follow_up_content = self.extract_content(
            intent=normalized_intent,
            previous_response=previous_response,
            include_evidence=include_evidence,
        )

        return {
            "request_id": previous_request_id,
            "conversation_id": normalized_conversation_id,
            "question": normalized_question,
            "intent": normalized_intent,
            "is_follow_up": True,
            "follow_up_intent": normalized_intent,
            "based_on_question": previous_question,
            "based_on_request_id": previous_request_id,
            "answer": follow_up_content,
            "confidence": previous_response.get("confidence"),
            "confidence_breakdown": self._dictionary(
                previous_response.get("confidence_breakdown")
            ),
            "warnings": self._list(previous_response.get("warnings")),
        }

    def extract_content(
        self,
        *,
        intent: str,
        previous_response: Mapping[str, Any],
        include_evidence: bool,
    ) -> dict[str, Any]:
        normalized_intent = self._normalize_required_text(
            intent,
            field_name="intent",
        )
        answer = self._mapping(previous_response.get("answer"))
        cognitive_execution = self._extract_execution(previous_response)

        if normalized_intent == "supporting_arguments":
            return self._supporting_arguments(
                previous_response=previous_response,
                answer=answer,
                include_evidence=include_evidence,
            )
        if normalized_intent == "hypothesis_review":
            return self._hypothesis_review(answer)
        if normalized_intent == "confidence_review":
            return self._confidence_review(
                previous_response=previous_response,
                cognitive_execution=cognitive_execution,
            )
        if normalized_intent == "contradiction_review":
            return self._contradiction_review(
                previous_response=previous_response,
                cognitive_execution=cognitive_execution,
            )
        if normalized_intent == "missing_knowledge_review":
            return self._missing_knowledge_review(
                previous_response=previous_response,
                answer=answer,
            )

        raise ValueError(
            f"Intention de suivi non prise en charge : {normalized_intent}."
        )

    def _supporting_arguments(
        self,
        *,
        previous_response: Mapping[str, Any],
        answer: Mapping[str, Any],
        include_evidence: bool,
    ) -> dict[str, Any]:
        evidence = (
            self._list(previous_response.get("evidence"))
            if include_evidence
            else []
        )
        sources = self._list(previous_response.get("sources"))
        if not sources:
            sources = self._list(answer.get("sources"))

        return {
            "summary": (
                "Voici les preuves et les sources utilisées pour "
                "construire la réponse précédente."
            ),
            "evidence": evidence,
            "sources": sources,
            "explicit_claims": self._list(answer.get("explicit_claims")),
            "deductions": self._list(answer.get("deductions")),
        }

    def _hypothesis_review(
        self,
        answer: Mapping[str, Any],
    ) -> dict[str, Any]:
        hypotheses = self._list(answer.get("hypotheses"))
        return {
            "summary": (
                "Voici les hypothèses formulées dans la réponse précédente."
            ),
            "hypotheses": hypotheses,
            "limitations": self.collect_claim_limitations(hypotheses),
        }

    def _confidence_review(
        self,
        *,
        previous_response: Mapping[str, Any],
        cognitive_execution: Mapping[str, Any],
    ) -> dict[str, Any]:
        trace = self._mapping(previous_response.get("trace"))
        return {
            "summary": (
                "Voici l'évaluation du niveau de confiance de la réponse précédente."
            ),
            "confidence": previous_response.get("confidence"),
            "confidence_breakdown": self._dictionary(
                previous_response.get("confidence_breakdown")
            ),
            "confidence_justification": cognitive_execution.get(
                "confidence_justification"
            ),
            "coverage_score": trace.get("coverage_score"),
        }

    def _contradiction_review(
        self,
        *,
        previous_response: Mapping[str, Any],
        cognitive_execution: Mapping[str, Any],
    ) -> dict[str, Any]:
        contradictions = self._list(cognitive_execution.get("contradictions"))
        if not contradictions:
            trace = self._mapping(previous_response.get("trace"))
            contradictions = self._list(trace.get("contradictions"))

        return {
            "summary": (
                "Voici les contradictions détectées dans la réponse précédente."
            ),
            "contradictions": contradictions,
            "contradiction_count": len(contradictions),
        }

    def _missing_knowledge_review(
        self,
        *,
        previous_response: Mapping[str, Any],
        answer: Mapping[str, Any],
    ) -> dict[str, Any]:
        missing_knowledge = self._list(
            previous_response.get("missing_knowledge")
        )
        if not missing_knowledge:
            missing_knowledge = self._list(answer.get("missing_knowledge"))

        warnings = self._list(previous_response.get("warnings"))
        if not warnings:
            warnings = self._list(answer.get("warnings"))

        return {
            "summary": (
                "Voici les connaissances manquantes ou les éléments "
                "qui n'ont pas pu être établis."
            ),
            "missing_knowledge": missing_knowledge,
            "unknowns": self._list(answer.get("unknowns")),
            "warnings": warnings,
        }

    @staticmethod
    def collect_claim_limitations(claims: Any) -> list[str]:
        if not isinstance(claims, (list, tuple)):
            return []

        limitations: list[str] = []
        seen: set[str] = set()

        for claim in claims:
            if not isinstance(claim, Mapping):
                continue
            claim_limitations = claim.get("limitations")
            if not isinstance(claim_limitations, (list, tuple)):
                continue

            for limitation in claim_limitations:
                normalized = FollowUpResponseBuilder._optional_text(limitation)
                if not normalized:
                    continue
                identity = normalized.casefold()
                if identity in seen:
                    continue
                seen.add(identity)
                limitations.append(normalized)

        return limitations

    @staticmethod
    def _extract_execution(
        previous_response: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        execution = previous_response.get("execution")
        if isinstance(execution, Mapping):
            return execution

        legacy_execution = previous_response.get("cognitive_execution")
        if isinstance(legacy_execution, Mapping):
            return legacy_execution

        return {}

    @staticmethod
    def _mapping(value: Any) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        return {}

    @staticmethod
    def _dictionary(value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        return {}

    @staticmethod
    def _list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return list(value)
        if isinstance(value, tuple):
            return list(value)
        return []

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        normalized = " ".join(str(value).strip().split())
        return normalized or None

    @staticmethod
    def _normalize_required_text(
        value: Any,
        *,
        field_name: str,
    ) -> str:
        normalized = FollowUpResponseBuilder._optional_text(value)
        if not normalized:
            raise ValueError(f"Le champ {field_name} ne peut pas être vide.")
        return normalized
