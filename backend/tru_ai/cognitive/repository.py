from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tru_ai.cognitive.models import CognitiveResponse
from tru_ai.memory.repository import MemoryRepository


class CognitiveRepository:
    """
    Gère :

    - la mémoire canonique de la TRU ;
    - l'enregistrement individuel des réponses cognitives ;
    - l'historique des conversations ;
    - la récupération de la dernière interaction d'une conversation.
    """

    def __init__(
        self,
        memory_repository: MemoryRepository,
        requests_directory: Path,
    ) -> None:
        self.memory_repository = memory_repository
        self.requests_directory = requests_directory

        # Les conversations sont enregistrées à côté des requêtes cognitives.
        #
        # Exemple :
        # corpus/cognitive/requests/
        # corpus/cognitive/conversations/
        self.conversations_directory = (
            self.requests_directory.parent / "conversations"
        )

    # ------------------------------------------------------------------
    # Mémoire canonique
    # ------------------------------------------------------------------

    def load_memory(self):
        """
        Charge la mémoire canonique.

        Si la mémoire n'existe pas encore, elle est reconstruite à partir
        des sources disponibles.
        """
        memory = self.memory_repository.load()

        if not memory.sources and not memory.elements:
            memory, _ = self.memory_repository.build()

        return memory

    # ------------------------------------------------------------------
    # Requêtes cognitives individuelles
    # ------------------------------------------------------------------

    def save_response(self, response: CognitiveResponse) -> None:
        """
        Enregistre une réponse cognitive individuelle dans un fichier JSON.
        """
        self.requests_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = self.requests_directory / f"{response.request_id}.json"

        payload = {
            "response": response.to_dict(include_evidence=True),
            "trace": response.trace.to_dict(),
        }

        self._write_json(
            path=path,
            payload=payload,
        )

    def load_request(self, request_id: str) -> dict | None:
        """
        Charge une requête cognitive enregistrée à partir de son identifiant.
        """
        path = self.requests_directory / f"{request_id}.json"

        if not path.exists():
            return None

        return self._read_json(path)

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    def create_conversation(self, conversation_id: str) -> dict:
        """
        Crée une nouvelle conversation vide.
        """
        now = self._utc_now()

        conversation: dict[str, Any] = {
            "conversation_id": conversation_id,
            "created_at": now,
            "updated_at": now,
            "last_request_id": None,
            "turn_count": 0,
            "turns": [],
        }

        self.save_conversation(conversation)

        return conversation

    def save_conversation(self, conversation: dict) -> None:
        """
        Enregistre l'état complet d'une conversation.
        """
        self.conversations_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        conversation_id = conversation.get("conversation_id")

        if not conversation_id:
            raise ValueError(
                "La conversation doit posséder un conversation_id."
            )

        path = self._conversation_path(conversation_id)

        self._write_json(
            path=path,
            payload=conversation,
        )

    def load_conversation(
        self,
        conversation_id: str,
    ) -> dict | None:
        """
        Charge une conversation à partir de son identifiant.
        """
        path = self._conversation_path(conversation_id)

        if not path.exists():
            return None

        return self._read_json(path)

    def conversation_exists(
        self,
        conversation_id: str,
    ) -> bool:
        """
        Vérifie si une conversation existe déjà.
        """
        return self._conversation_path(conversation_id).exists()

    def append_conversation_turn(
        self,
        conversation_id: str,
        question: str,
        intent: str,
        response: CognitiveResponse | dict,
        *,
        is_follow_up: bool = False,
        follow_up_intent: str | None = None,
    ) -> dict:
        """
        Ajoute une interaction complète dans une conversation.

        Une interaction contient :

        - la question de l'utilisateur ;
        - l'intention détectée ;
        - l'identifiant de la réponse cognitive ;
        - la réponse cognitive sérialisée ;
        - l'indication qu'il s'agit ou non d'une question de suivi.
        """
        conversation = self.load_conversation(conversation_id)

        if conversation is None:
            conversation = self.create_conversation(conversation_id)

        response_payload = self._serialize_response(response)

        request_id = response_payload.get("request_id")

        turn = {
            "turn_index": len(conversation.get("turns", [])) + 1,
            "created_at": self._utc_now(),
            "question": question,
            "intent": intent,
            "is_follow_up": is_follow_up,
            "follow_up_intent": follow_up_intent,
            "request_id": request_id,
            "response": response_payload,
        }

        conversation.setdefault("turns", []).append(turn)

        conversation["turn_count"] = len(conversation["turns"])
        conversation["last_request_id"] = request_id
        conversation["updated_at"] = self._utc_now()

        self.save_conversation(conversation)

        return turn

    def get_last_conversation_turn(
        self,
        conversation_id: str,
    ) -> dict | None:
        """
        Retourne la dernière interaction enregistrée dans une conversation.
        """
        conversation = self.load_conversation(conversation_id)

        if conversation is None:
            return None

        turns = conversation.get("turns", [])

        if not turns:
            return None

        return turns[-1]

    def get_last_conversation_response(
        self,
        conversation_id: str,
    ) -> dict | None:
        """
        Retourne uniquement la dernière réponse cognitive sérialisée.
        """
        last_turn = self.get_last_conversation_turn(conversation_id)

        if last_turn is None:
            return None

        response = last_turn.get("response")

        if not isinstance(response, dict):
            return None

        return response

    def list_conversation_turns(
        self,
        conversation_id: str,
    ) -> list[dict]:
        """
        Retourne toutes les interactions d'une conversation.
        """
        conversation = self.load_conversation(conversation_id)

        if conversation is None:
            return []

        turns = conversation.get("turns", [])

        if not isinstance(turns, list):
            return []

        return turns

    def delete_conversation(
        self,
        conversation_id: str,
    ) -> bool:
        """
        Supprime une conversation.

        Retourne True si le fichier existait, sinon False.
        """
        path = self._conversation_path(conversation_id)

        if not path.exists():
            return False

        path.unlink()

        return True

    def clear_conversations(self) -> int:
        """
        Supprime toutes les conversations enregistrées.

        Retourne le nombre de fichiers supprimés.
        """
        if not self.conversations_directory.exists():
            return 0

        deleted_count = 0

        for path in self.conversations_directory.glob("*.json"):
            path.unlink()
            deleted_count += 1

        return deleted_count

    # ------------------------------------------------------------------
    # Méthodes internes
    # ------------------------------------------------------------------

    def _conversation_path(
        self,
        conversation_id: str,
    ) -> Path:
        """
        Construit le chemin sécurisé d'une conversation.
        """
        safe_conversation_id = "".join(
            character
            for character in conversation_id
            if character.isalnum() or character in ("-", "_")
        )

        if not safe_conversation_id:
            raise ValueError(
                "Identifiant de conversation invalide."
            )

        return (
            self.conversations_directory
            / f"{safe_conversation_id}.json"
        )

    def _serialize_response(
        self,
        response: CognitiveResponse | dict,
    ) -> dict:
        """
        Transforme une réponse cognitive en dictionnaire JSON.
        """
        if isinstance(response, CognitiveResponse):
            return response.to_dict(include_evidence=True)

        if isinstance(response, dict):
            return dict(response)

        raise TypeError(
            "La réponse doit être une CognitiveResponse ou un dictionnaire."
        )

    def _read_json(
        self,
        path: Path,
    ) -> dict:
        """
        Lit un fichier JSON.
        """
        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def _write_json(
        self,
        path: Path,
        payload: dict[str, Any],
    ) -> None:
        """
        Écrit un dictionnaire dans un fichier JSON.
        """
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open("w", encoding="utf-8") as output_file:
            json.dump(
                payload,
                output_file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

            output_file.write("\n")

    def _utc_now(self) -> str:
        """
        Retourne la date actuelle au format ISO 8601 en UTC.
        """
        return datetime.now(timezone.utc).isoformat()
