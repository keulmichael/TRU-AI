from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from tru_ai.cognitive.conversation.context_builder import (
    ConversationContext,
    ConversationContextBuilder,
)
from tru_ai.cognitive.conversation.follow_up import (
    FollowUpResponseBuilder,
)
from tru_ai.cognitive.conversation.models import (
    ConversationPipelineRequest,
    ConversationPipelineResult,
    ConversationProcessingTrace,
)
from tru_ai.cognitive.conversation.question_rewriter import (
    QuestionRewriter,
)
from tru_ai.cognitive.conversation.reference_resolver import (
    ReferenceResolver,
)
from tru_ai.cognitive.core import CognitiveCore
from tru_ai.cognitive.intent import IntentDetector
from tru_ai.cognitive.reasoning.executor import ReasoningExecutor
from tru_ai.cognitive.reasoning.models import ReasoningRequest
from tru_ai.cognitive.reasoning.planner import ReasoningPlanner
from tru_ai.cognitive.repository import CognitiveRepository


class ConversationPipeline:
    """
    Orchestre une interaction conversationnelle complète.

    Ordre d'exécution :

    1. normaliser et valider la question ;
    2. créer ou charger la conversation ;
    3. construire le contexte conversationnel ;
    4. détecter les demandes de suivi spécialisées ;
    5. résoudre les références implicites ;
    6. réécrire la question en demande autonome ;
    7. construire le plan de raisonnement ;
    8. exécuter le plan de raisonnement ;
    9. interroger le CognitiveCore ;
    10. persister la réponse et le nouveau tour.

    La couche HTTP ne dépend que du ConversationService. Le pipeline reste
    indépendant de FastAPI et peut donc être testé ou réutilisé directement.
    """

    def __init__(
        self,
        *,
        repository: CognitiveRepository,
        core: CognitiveCore,
        intent_detector: IntentDetector | None = None,
        context_builder: ConversationContextBuilder | None = None,
        reference_resolver: ReferenceResolver | None = None,
        question_rewriter: QuestionRewriter | None = None,
        follow_up_builder: FollowUpResponseBuilder | None = None,
        reasoning_planner: ReasoningPlanner | None = None,
        reasoning_executor: ReasoningExecutor | None = None,
    ) -> None:
        self.repository = repository
        self.core = core
        self.intent_detector = intent_detector or IntentDetector()
        self.context_builder = context_builder or ConversationContextBuilder()
        self.reference_resolver = reference_resolver or ReferenceResolver()
        self.question_rewriter = question_rewriter or QuestionRewriter()
        self.follow_up_builder = follow_up_builder or FollowUpResponseBuilder()
        self.reasoning_planner = reasoning_planner or ReasoningPlanner()
        self.reasoning_executor = reasoning_executor or ReasoningExecutor()

    def ask(
        self,
        request: ConversationPipelineRequest,
    ) -> ConversationPipelineResult:
        question = request.normalized_question()

        if not question:
            raise ValueError("La question ne peut pas être vide.")

        conversation_id, conversation = self._get_or_create_conversation(
            request.conversation_id
        )
        context = self.context_builder.build(conversation)
        intent = self.intent_detector.detect(question)
        previous_turn = self.repository.get_last_conversation_turn(
            conversation_id
        )

        if self._is_specialized_follow_up(
            intent=intent,
            previous_turn=previous_turn,
        ):
            return self._answer_follow_up(
                conversation_id=conversation_id,
                question=question,
                intent=intent,
                previous_turn=previous_turn,
                include_evidence=request.include_evidence,
                context=context,
            )

        resolution = self.reference_resolver.resolve(
            question,
            context,
        )
        rewrite = self.question_rewriter.rewrite(
            question=question,
            context=context,
            resolution=resolution,
        )

        effective_question = (
            rewrite.rewritten_question.strip()
            or question
        )
        effective_intent = self.intent_detector.detect(effective_question)

        reasoning_plan = self.reasoning_planner.plan(
            ReasoningRequest(
                question=effective_question,
                intent=effective_intent,
                conversation_context=context.to_dict(),
            )
        )
        reasoning_result = self.reasoning_executor.execute(
            reasoning_plan,
            conversation_context=context.to_dict(),
        )

        response = self.core.ask(
            effective_question,
            include_evidence=request.include_evidence,
        )
        self.repository.save_response(response)

        payload = response.to_dict(
            include_evidence=request.include_evidence
        )
        payload.update(
            {
                "intent": effective_intent,
                "is_follow_up": False,
                "original_question": question,
                "rewritten_question": effective_question,
                "was_rewritten": rewrite.was_rewritten,
                "reasoning_plan": reasoning_plan.to_dict(),
                "reasoning_result": reasoning_result.to_dict(),
            }
        )
        payload["warnings"] = self._merge_warnings(
            payload.get("warnings"),
            rewrite.warnings,
        )

        self.repository.append_conversation_turn(
            conversation_id=conversation_id,
            question=question,
            intent=effective_intent,
            response=response,
            is_follow_up=False,
        )

        processing = ConversationProcessingTrace(
            original_question=question,
            effective_question=effective_question,
            detected_intent=effective_intent,
            is_follow_up=False,
            context=context.to_dict(),
            reference_resolution=resolution.to_dict(),
            question_rewrite=rewrite.to_dict(),
            reasoning_plan=reasoning_plan.to_dict(),
            reasoning_result=reasoning_result.to_dict(),
        )

        return ConversationPipelineResult(
            conversation_id=conversation_id,
            payload=payload,
            processing=processing,
        )

    def _answer_follow_up(
        self,
        *,
        conversation_id: str,
        question: str,
        intent: str,
        previous_turn: dict[str, Any],
        include_evidence: bool,
        context: ConversationContext,
    ) -> ConversationPipelineResult:
        payload = self.follow_up_builder.build(
            conversation_id=conversation_id,
            question=question,
            intent=intent,
            previous_turn=previous_turn,
            include_evidence=include_evidence,
        )

        self.repository.append_conversation_turn(
            conversation_id=conversation_id,
            question=question,
            intent=intent,
            response=payload,
            is_follow_up=True,
            follow_up_intent=intent,
        )

        processing = ConversationProcessingTrace(
            original_question=question,
            effective_question=question,
            detected_intent=intent,
            is_follow_up=True,
            context=context.to_dict(),
            reference_resolution=None,
            question_rewrite=None,
            reasoning_plan=None,
            reasoning_result=None,
        )

        return ConversationPipelineResult(
            conversation_id=conversation_id,
            payload=payload,
            processing=processing,
        )

    def _get_or_create_conversation(
        self,
        requested_conversation_id: str | None,
    ) -> tuple[str, dict[str, Any]]:
        requested = str(requested_conversation_id or "").strip()
        conversation_id = requested or str(uuid4())

        conversation = self.repository.load_conversation(conversation_id)

        if conversation is None:
            conversation = self.repository.create_conversation(
                conversation_id
            )

        return conversation_id, conversation

    def _is_specialized_follow_up(
        self,
        *,
        intent: str,
        previous_turn: dict[str, Any] | None,
    ) -> bool:
        return (
            previous_turn is not None
            and self.follow_up_builder.is_follow_up_intent(intent)
        )

    @staticmethod
    def _merge_warnings(
        existing: Any,
        additional: Iterable[str],
    ) -> list[str]:
        values: list[str] = []

        if isinstance(existing, (list, tuple)):
            values.extend(
                value
                for value in existing
                if isinstance(value, str)
            )

        values.extend(
            value
            for value in additional
            if isinstance(value, str)
        )

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = " ".join(value.strip().split())
            identity = normalized.casefold()

            if not normalized or identity in seen:
                continue

            seen.add(identity)
            result.append(normalized)

        return result
