from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ConversationContext:
    """
    Représentation synthétique et déterministe d'une conversation.

    Cette structure ne produit aucun raisonnement nouveau. Elle rassemble
    uniquement les informations déjà présentes dans l'historique afin de les
    rendre exploitables par les futures couches conversationnelles.
    """

    conversation_id: str
    turn_count: int
    main_subject: str | None
    current_question: str | None
    previous_question: str | None
    last_independent_question: str | None
    last_follow_up_intent: str | None
    concepts: tuple[str, ...]
    explicit_claims: tuple[str, ...]
    deductions: tuple[str, ...]
    hypotheses: tuple[str, ...]
    unknowns: tuple[str, ...]
    missing_knowledge: tuple[str, ...]
    warnings: tuple[str, ...]
    recent_questions: tuple[str, ...]
    recent_summaries: tuple[str, ...]
    request_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConversationContextBuilder:
    """
    Construit un contexte conversationnel à partir d'une conversation
    persistée par le CognitiveRepository.

    Le builder accepte volontairement des dictionnaires génériques afin de
    rester indépendant des modèles de persistance et de supporter les
    évolutions futures du format des conversations.
    """

    def __init__(self, *, recent_turn_limit: int = 8) -> None:
        if recent_turn_limit < 1:
            raise ValueError("recent_turn_limit doit être supérieur ou égal à 1.")

        self.recent_turn_limit = recent_turn_limit

    def build(
        self,
        conversation: Mapping[str, Any],
    ) -> ConversationContext:
        conversation_id = self._string_value(
            conversation.get("conversation_id")
            or conversation.get("id")
        )

        turns = self._normalize_turns(conversation.get("turns"))
        recent_turns = turns[-self.recent_turn_limit :]

        current_turn = recent_turns[-1] if recent_turns else None
        previous_turn = recent_turns[-2] if len(recent_turns) >= 2 else None

        current_question = self._question_from_turn(current_turn)
        previous_question = self._question_from_turn(previous_turn)

        last_independent_question = self._last_independent_question(turns)
        last_follow_up_intent = self._last_follow_up_intent(turns)

        concepts: list[str] = []
        explicit_claims: list[str] = []
        deductions: list[str] = []
        hypotheses: list[str] = []
        unknowns: list[str] = []
        missing_knowledge: list[str] = []
        warnings: list[str] = []
        summaries: list[str] = []
        request_ids: list[str] = []

        for turn in recent_turns:
            response = self._response_from_turn(turn)

            concepts.extend(self._extract_concepts(response))
            explicit_claims.extend(
                self._extract_classification(response, "EXPLICITE")
            )
            deductions.extend(
                self._extract_classification(response, "DÉDUCTION")
            )
            hypotheses.extend(
                self._extract_classification(response, "HYPOTHÈSE")
            )
            unknowns.extend(
                self._extract_classification(response, "INCONNU")
            )
            missing_knowledge.extend(
                self._string_sequence(response.get("missing_knowledge"))
            )
            warnings.extend(
                self._string_sequence(response.get("warnings"))
            )

            summary = self._extract_summary(response)
            if summary:
                summaries.append(summary)

            request_id = self._string_value(response.get("request_id"))
            if request_id:
                request_ids.append(request_id)

        recent_questions = tuple(
            question
            for question in (
                self._question_from_turn(turn)
                for turn in recent_turns
            )
            if question
        )

        main_subject = self._resolve_main_subject(
            turns=turns,
            concepts=concepts,
        )

        return ConversationContext(
            conversation_id=conversation_id or "",
            turn_count=len(turns),
            main_subject=main_subject,
            current_question=current_question,
            previous_question=previous_question,
            last_independent_question=last_independent_question,
            last_follow_up_intent=last_follow_up_intent,
            concepts=self._unique(concepts),
            explicit_claims=self._unique(explicit_claims),
            deductions=self._unique(deductions),
            hypotheses=self._unique(hypotheses),
            unknowns=self._unique(unknowns),
            missing_knowledge=self._unique(missing_knowledge),
            warnings=self._unique(warnings),
            recent_questions=self._unique(recent_questions),
            recent_summaries=self._unique(summaries),
            request_ids=self._unique(request_ids),
        )

    @staticmethod
    def empty(conversation_id: str = "") -> ConversationContext:
        return ConversationContext(
            conversation_id=conversation_id,
            turn_count=0,
            main_subject=None,
            current_question=None,
            previous_question=None,
            last_independent_question=None,
            last_follow_up_intent=None,
            concepts=(),
            explicit_claims=(),
            deductions=(),
            hypotheses=(),
            unknowns=(),
            missing_knowledge=(),
            warnings=(),
            recent_questions=(),
            recent_summaries=(),
            request_ids=(),
        )

    def _resolve_main_subject(
        self,
        *,
        turns: Sequence[Mapping[str, Any]],
        concepts: Sequence[str],
    ) -> str | None:
        """
        Le sujet principal est déterminé sans inventer de contenu.

        Priorité :
        1. le premier concept reconnu dans les réponses ;
        2. la dernière question indépendante ;
        3. la première question de la conversation.
        """

        unique_concepts = self._unique(concepts)
        if unique_concepts:
            return unique_concepts[0]

        independent_question = self._last_independent_question(turns)
        if independent_question:
            return independent_question

        for turn in turns:
            question = self._question_from_turn(turn)
            if question:
                return question

        return None

    def _last_independent_question(
        self,
        turns: Sequence[Mapping[str, Any]],
    ) -> str | None:
        for turn in reversed(turns):
            if not self._is_follow_up(turn):
                question = self._question_from_turn(turn)
                if question:
                    return question

        return None

    def _last_follow_up_intent(
        self,
        turns: Sequence[Mapping[str, Any]],
    ) -> str | None:
        for turn in reversed(turns):
            if not self._is_follow_up(turn):
                continue

            intent = self._string_value(turn.get("follow_up_intent"))
            if intent:
                return intent

            response = self._response_from_turn(turn)
            intent = self._string_value(response.get("follow_up_intent"))
            if intent:
                return intent

        return None

    @staticmethod
    def _normalize_turns(value: Any) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, Sequence) or isinstance(
            value,
            (str, bytes, bytearray),
        ):
            return ()

        return tuple(
            item
            for item in value
            if isinstance(item, Mapping)
        )

    @staticmethod
    def _question_from_turn(
        turn: Mapping[str, Any] | None,
    ) -> str | None:
        if not turn:
            return None

        for key in (
            "question",
            "user_question",
            "original_question",
            "message",
        ):
            value = ConversationContextBuilder._string_value(turn.get(key))
            if value:
                return value

        request = turn.get("request")
        if isinstance(request, Mapping):
            for key in ("question", "message"):
                value = ConversationContextBuilder._string_value(
                    request.get(key)
                )
                if value:
                    return value

        response = ConversationContextBuilder._response_from_turn(turn)

        trace = response.get("trace")
        if isinstance(trace, Mapping):
            value = ConversationContextBuilder._string_value(
                trace.get("original_question")
            )
            if value:
                return value

        execution = response.get("execution")
        if isinstance(execution, Mapping):
            value = ConversationContextBuilder._string_value(
                execution.get("question")
            )
            if value:
                return value

        return None

    @staticmethod
    def _response_from_turn(
        turn: Mapping[str, Any] | None,
    ) -> Mapping[str, Any]:
        if not turn:
            return {}

        for key in (
            "response",
            "cognitive_response",
            "result",
        ):
            value = turn.get(key)
            if isinstance(value, Mapping):
                return value

        if any(
            key in turn
            for key in (
                "request_id",
                "answer",
                "classifications",
                "execution",
                "trace",
            )
        ):
            return turn

        return {}

    @staticmethod
    def _is_follow_up(turn: Mapping[str, Any]) -> bool:
        value = turn.get("is_follow_up")

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {
                "true",
                "1",
                "yes",
                "oui",
            }

        response = ConversationContextBuilder._response_from_turn(turn)
        response_value = response.get("is_follow_up")

        if isinstance(response_value, bool):
            return response_value

        return bool(turn.get("follow_up_intent"))

    def _extract_concepts(
        self,
        response: Mapping[str, Any],
    ) -> tuple[str, ...]:
        concepts: list[str] = []

        execution = response.get("execution")
        if isinstance(execution, Mapping):
            concepts.extend(
                self._string_sequence(
                    execution.get("concepts_recognized")
                )
            )

        trace = response.get("trace")
        if isinstance(trace, Mapping):
            concepts.extend(
                self._string_sequence(
                    trace.get("detected_concepts")
                )
            )
            concepts.extend(
                self._string_sequence(
                    trace.get("selected_concepts")
                )
            )

        concepts.extend(
            self._string_sequence(response.get("concepts"))
        )

        return self._unique(concepts)

    def _extract_classification(
        self,
        response: Mapping[str, Any],
        classification_name: str,
    ) -> tuple[str, ...]:
        classifications = response.get("classifications")

        if not isinstance(classifications, Mapping):
            return ()

        raw_claims = classifications.get(classification_name)

        if not isinstance(raw_claims, Sequence) or isinstance(
            raw_claims,
            (str, bytes, bytearray),
        ):
            return ()

        claims: list[str] = []

        for claim in raw_claims:
            text = self._claim_text(claim)
            if text:
                claims.append(text)

        return self._unique(claims)

    @staticmethod
    def _claim_text(value: Any) -> str | None:
        if isinstance(value, str):
            return ConversationContextBuilder._string_value(value)

        if not isinstance(value, Mapping):
            return None

        for key in (
            "text",
            "claim",
            "content",
            "statement",
            "summary",
        ):
            text = ConversationContextBuilder._string_value(value.get(key))
            if text:
                return text

        return None

    @staticmethod
    def _extract_summary(
        response: Mapping[str, Any],
    ) -> str | None:
        answer = response.get("answer")

        if isinstance(answer, Mapping):
            for key in (
                "summary",
                "final_answer",
                "text",
                "content",
            ):
                value = ConversationContextBuilder._string_value(
                    answer.get(key)
                )
                if value:
                    return value

        execution = response.get("execution")
        if isinstance(execution, Mapping):
            value = ConversationContextBuilder._string_value(
                execution.get("final_answer")
            )
            if value:
                return value

        return None

    @staticmethod
    def _string_sequence(value: Any) -> tuple[str, ...]:
        if value is None:
            return ()

        if isinstance(value, str):
            normalized = ConversationContextBuilder._string_value(value)
            return (normalized,) if normalized else ()

        if not isinstance(value, Iterable):
            return ()

        values: list[str] = []

        for item in value:
            if isinstance(item, str):
                normalized = ConversationContextBuilder._string_value(item)
                if normalized:
                    values.append(normalized)
                continue

            if isinstance(item, Mapping):
                text = ConversationContextBuilder._claim_text(item)
                if text:
                    values.append(text)

        return tuple(values)

    @staticmethod
    def _string_value(value: Any) -> str | None:
        if value is None:
            return None

        normalized = " ".join(str(value).strip().split())
        return normalized or None

    @staticmethod
    def _unique(values: Iterable[str]) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = ConversationContextBuilder._string_value(value)
            if not normalized:
                continue

            identity = normalized.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(normalized)

        return tuple(result)