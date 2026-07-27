from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tru_ai.cognitive.conversation.pipeline import ConversationPipeline
from tru_ai.cognitive.conversation.service import ConversationService
from tru_ai.cognitive.core import CognitiveCore
from tru_ai.cognitive.repository import CognitiveRepository
from tru_ai.memory.repository import MemoryRepository


PROJECT_ROOT = Path(__file__).resolve().parents[3]

SOURCES_DIRECTORY = PROJECT_ROOT / "corpus" / "sources"
DEMO_DIRECTORY = PROJECT_ROOT / "corpus" / "raw"
MEMORY_DIRECTORY = PROJECT_ROOT / "corpus" / "memory"
REQUESTS_DIRECTORY = (
    PROJECT_ROOT
    / "corpus"
    / "cognitive"
    / "requests"
)


router = APIRouter(
    prefix="/cognitive",
    tags=["Cognitive Core"],
)


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="Question adressée au Cognitive Core.",
    )

    include_evidence: bool = Field(
        default=True,
        description="Inclure ou non les preuves dans la réponse.",
    )

    conversation_id: str | None = Field(
        default=None,
        description=(
            "Identifiant d'une conversation existante. "
            "Laisser vide pour créer une nouvelle conversation."
        ),
    )


@lru_cache(maxsize=1)
def get_repository() -> CognitiveRepository:
    return CognitiveRepository(
        memory_repository=MemoryRepository(
            sources_directory=SOURCES_DIRECTORY,
            memory_directory=MEMORY_DIRECTORY,
            demo_directory=DEMO_DIRECTORY,
        ),
        requests_directory=REQUESTS_DIRECTORY,
    )


@lru_cache(maxsize=1)
def get_core() -> CognitiveCore:
    return CognitiveCore(
        get_repository().load_memory()
    )


@lru_cache(maxsize=1)
def get_conversation_pipeline() -> ConversationPipeline:
    return ConversationPipeline(
        repository=get_repository(),
        core=get_core(),
    )


@lru_cache(maxsize=1)
def get_conversation_service() -> ConversationService:
    return ConversationService(
        repository=get_repository(),
        pipeline=get_conversation_pipeline(),
    )


@router.get("/health")
def health() -> dict:
    try:
        memory = get_repository().load_memory()

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "status": "ok",
        "loaded": True,
        "source_count": len(memory.sources),
        "memory_element_count": len(memory.elements),
        "production_source_count": len(
            [
                source
                for source in memory.sources
                if not source.is_demo_source
            ]
        ),
    }


@router.get("/capabilities")
def capabilities() -> dict:
    return {
        "capabilities": [
            {
                "id": "concept_explanation",
                "name": "Expliquer un concept de la TRU",
                "status": "alpha",
            },
            {
                "id": "applied_analysis",
                "name": "Analyse appliquée contrôlée",
                "status": "alpha",
            },
            {
                "id": "conversation",
                "name": "Conversation cognitive simplifiée",
                "status": "alpha",
            },
        ],
        "follow_up_capabilities": [
            {
                "id": "supporting_arguments",
                "name": "Revoir les preuves et arguments",
            },
            {
                "id": "hypothesis_review",
                "name": "Revoir les hypothèses",
            },
            {
                "id": "confidence_review",
                "name": "Revoir le niveau de confiance",
            },
            {
                "id": "contradiction_review",
                "name": "Revoir les contradictions",
            },
            {
                "id": "missing_knowledge_review",
                "name": "Revoir les connaissances manquantes",
            },
        ],
        "truth_policy": [
            "EXPLICITE",
            "DÉDUCTION",
            "HYPOTHÈSE",
            "INCONNU",
        ],
        "llm_required": False,
    }


@router.post("/ask")
def ask(payload: AskRequest) -> dict:
    """
    Pose une question au système conversationnel cognitif.

    Le routeur valide la requête HTTP puis délègue l'ensemble du traitement
    au ConversationService et au ConversationPipeline.
    """
    try:
        return get_conversation_service().ask(
            question=payload.question,
            include_evidence=payload.include_evidence,
            conversation_id=payload.conversation_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
) -> dict:
    """
    Retourne l'historique complet d'une conversation.
    """
    try:
        conversation = (
            get_conversation_service()
            .get_conversation(conversation_id)
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation introuvable.",
            )

        return conversation

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.get("/conversations/{conversation_id}/last")
def get_last_conversation_turn(
    conversation_id: str,
) -> dict:
    """
    Retourne la dernière interaction d'une conversation.
    """
    try:
        last_turn = (
            get_conversation_service()
            .get_last_conversation_turn(conversation_id)
        )

        if last_turn is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Conversation introuvable ou sans interaction."
                ),
            )

        return last_turn

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
) -> dict:
    """
    Supprime une conversation enregistrée.
    """
    try:
        deleted = (
            get_conversation_service()
            .delete_conversation(conversation_id)
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Conversation introuvable.",
            )

        return {
            "status": "deleted",
            "conversation_id": conversation_id,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.get("/requests/{request_id}")
def get_request(
    request_id: str,
) -> dict:
    record = get_conversation_service().get_request(request_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Requête cognitive introuvable.",
        )

    return record


@router.get("/requests/{request_id}/evidence")
def get_request_evidence(
    request_id: str,
) -> dict:
    result = (
        get_conversation_service()
        .get_request_evidence(request_id)
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Requête cognitive introuvable.",
        )

    return result


@router.post("/reload")
def reload() -> dict:
    """
    Recharge le Cognitive Core et la mémoire canonique.

    Les conversations enregistrées sur le disque sont conservées.
    """
    get_conversation_service.cache_clear()
    get_conversation_pipeline.cache_clear()
    get_core.cache_clear()
    get_repository.cache_clear()

    return health()
