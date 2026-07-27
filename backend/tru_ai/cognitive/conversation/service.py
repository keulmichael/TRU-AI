from __future__ import annotations

from typing import Any

from tru_ai.cognitive.conversation.models import (
    ConversationPipelineRequest,
)
from tru_ai.cognitive.conversation.pipeline import ConversationPipeline
from tru_ai.cognitive.repository import CognitiveRepository


class ConversationService:
    """
    Façade applicative du module conversationnel.

    Le service constitue l'unique point d'entrée utilisé par la couche HTTP.
    Il délègue la production d'une réponse au ConversationPipeline et regroupe
    les opérations de consultation ou de suppression liées aux conversations
    et aux requêtes cognitives persistées.

    Il ne contient aucune logique HTTP : les codes de statut et les
    HTTPException restent de la responsabilité de l'API FastAPI.
    """

    def __init__(
        self,
        *,
        repository: CognitiveRepository,
        pipeline: ConversationPipeline,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline

    def ask(
        self,
        *,
        question: str,
        include_evidence: bool = True,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Exécute une interaction conversationnelle complète.
        """
        request = ConversationPipelineRequest(
            question=question,
            include_evidence=include_evidence,
            conversation_id=conversation_id,
        )

        return self.pipeline.ask(request).to_dict()

    def get_conversation(
        self,
        conversation_id: str,
    ) -> dict[str, Any] | None:
        """
        Retourne une conversation persistée, lorsqu'elle existe.
        """
        return self.repository.load_conversation(conversation_id)

    def get_last_conversation_turn(
        self,
        conversation_id: str,
    ) -> dict[str, Any] | None:
        """
        Retourne la dernière interaction d'une conversation.
        """
        return self.repository.get_last_conversation_turn(conversation_id)

    def delete_conversation(
        self,
        conversation_id: str,
    ) -> bool:
        """
        Supprime une conversation persistée.
        """
        return self.repository.delete_conversation(conversation_id)

    def get_request(
        self,
        request_id: str,
    ) -> dict[str, Any] | None:
        """
        Retourne une requête cognitive persistée.
        """
        return self.repository.load_request(request_id)

    def get_request_evidence(
        self,
        request_id: str,
    ) -> dict[str, Any] | None:
        """
        Retourne les preuves et la trace d'une requête cognitive.
        """
        record = self.get_request(request_id)

        if record is None:
            return None

        response = record.get("response", {})
        trace = record.get("trace", {})

        if not isinstance(response, dict):
            response = {}

        if not isinstance(trace, dict):
            trace = {}

        evidence = response.get("evidence", [])

        if not isinstance(evidence, list):
            evidence = []

        return {
            "request_id": request_id,
            "evidence": evidence,
            "trace": trace,
        }
