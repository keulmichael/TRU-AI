from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any
from uuid import uuid4


_conversations: dict[str, list[dict[str, Any]]] = {}
_lock = Lock()


def create_conversation() -> str:
    """Crée une nouvelle conversation et retourne son identifiant."""
    conversation_id = str(uuid4())

    with _lock:
        _conversations[conversation_id] = []

    return conversation_id


def conversation_exists(conversation_id: str) -> bool:
    """Indique si la conversation existe dans la mémoire de travail."""
    with _lock:
        return conversation_id in _conversations


def append_execution(
    conversation_id: str,
    execution: dict[str, Any],
) -> None:
    """Ajoute une exécution cognitive à une conversation."""
    with _lock:
        _conversations.setdefault(conversation_id, []).append(
            deepcopy(execution)
        )


def get_last_execution(
    conversation_id: str,
) -> dict[str, Any] | None:
    """Retourne la dernière exécution cognitive de la conversation."""
    with _lock:
        executions = _conversations.get(conversation_id, [])

        if not executions:
            return None

        return deepcopy(executions[-1])


def get_conversation_history(
    conversation_id: str,
) -> list[dict[str, Any]]:
    """Retourne l’historique complet d’une conversation."""
    with _lock:
        return deepcopy(_conversations.get(conversation_id, []))


def clear_conversation(conversation_id: str) -> None:
    """Supprime une conversation de la mémoire de travail."""
    with _lock:
        _conversations.pop(conversation_id, None)