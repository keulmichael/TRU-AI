from __future__ import annotations

import pytest

from tru_ai.cognitive.conversation.context_builder import (
    ConversationContext,
    ConversationContextBuilder,
)


def make_response(
    *,
    request_id: str,
    concepts: tuple[str, ...] = (),
    explicit_claims: tuple[str, ...] = (),
    deductions: tuple[str, ...] = (),
    hypotheses: tuple[str, ...] = (),
    unknowns: tuple[str, ...] = (),
    missing_knowledge: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    summary: str = "",
) -> dict:
    return {
        "request_id": request_id,
        "answer": {
            "summary": summary,
        },
        "classifications": {
            "EXPLICITE": [
                {
                    "claim_id": f"explicit-{index}",
                    "text": text,
                }
                for index, text in enumerate(
                    explicit_claims,
                    start=1,
                )
            ],
            "DÉDUCTION": [
                {
                    "claim_id": f"deduction-{index}",
                    "text": text,
                }
                for index, text in enumerate(
                    deductions,
                    start=1,
                )
            ],
            "HYPOTHÈSE": [
                {
                    "claim_id": f"hypothesis-{index}",
                    "text": text,
                }
                for index, text in enumerate(
                    hypotheses,
                    start=1,
                )
            ],
            "INCONNU": [
                {
                    "claim_id": f"unknown-{index}",
                    "text": text,
                }
                for index, text in enumerate(
                    unknowns,
                    start=1,
                )
            ],
        },
        "missing_knowledge": list(missing_knowledge),
        "warnings": list(warnings),
        "execution": {
            "question": "",
            "concepts_recognized": list(concepts),
            "final_answer": summary,
        },
        "trace": {
            "detected_concepts": list(concepts),
            "selected_concepts": list(concepts),
        },
    }


def make_turn(
    *,
    turn_index: int,
    question: str,
    intent: str,
    response: dict,
    is_follow_up: bool = False,
    follow_up_intent: str | None = None,
) -> dict:
    return {
        "turn_index": turn_index,
        "created_at": f"2026-07-25T20:00:0{turn_index}+00:00",
        "question": question,
        "intent": intent,
        "is_follow_up": is_follow_up,
        "follow_up_intent": follow_up_intent,
        "request_id": response["request_id"],
        "response": response,
    }


def test_empty_context_contains_no_conversation_data():
    context = ConversationContextBuilder.empty(
        conversation_id="conversation-empty"
    )

    assert isinstance(context, ConversationContext)
    assert context.conversation_id == "conversation-empty"
    assert context.turn_count == 0
    assert context.main_subject is None
    assert context.current_question is None
    assert context.previous_question is None
    assert context.last_independent_question is None
    assert context.last_follow_up_intent is None
    assert context.concepts == ()
    assert context.explicit_claims == ()
    assert context.deductions == ()
    assert context.hypotheses == ()
    assert context.unknowns == ()
    assert context.missing_knowledge == ()
    assert context.warnings == ()
    assert context.recent_questions == ()
    assert context.recent_summaries == ()
    assert context.request_ids == ()


def test_builder_rejects_invalid_recent_turn_limit():
    with pytest.raises(
        ValueError,
        match="recent_turn_limit doit être supérieur ou égal à 1",
    ):
        ConversationContextBuilder(recent_turn_limit=0)


def test_builder_extracts_context_from_repository_conversation():
    first_response = make_response(
        request_id="cognitive-request-burnout",
        concepts=("burn-out", "Delta", "reconnaissance"),
        explicit_claims=(
            "Le burn-out peut être étudié comme un processus d'épuisement.",
        ),
        deductions=(
            "Un écart durable entre l'état vécu et l'état attendu "
            "peut renforcer la tension.",
        ),
        hypotheses=(
            "Le Delta pourrait contribuer à modéliser cet écart.",
        ),
        unknowns=(
            "Le rôle causal exact du Delta reste à démontrer.",
        ),
        missing_knowledge=(
            "Des données cliniques comparatives sont nécessaires.",
        ),
        warnings=(
            "La TRU ne remplace pas un diagnostic médical.",
        ),
        summary=(
            "Le burn-out est analysé comme une accumulation d'écarts "
            "non reconnus."
        ),
    )

    second_response = make_response(
        request_id="cognitive-request-burnout",
        concepts=("burn-out", "Delta"),
        hypotheses=(
            "Le Delta pourrait contribuer à modéliser cet écart.",
            "La répétition de l'écart pourrait participer à l'épuisement.",
        ),
        summary=(
            "Deux hypothèses principales relient le Delta "
            "à l'épuisement."
        ),
    )

    conversation = {
        "conversation_id": "conversation-burnout",
        "created_at": "2026-07-25T20:00:00+00:00",
        "updated_at": "2026-07-25T20:01:00+00:00",
        "last_request_id": "cognitive-request-burnout",
        "turn_count": 2,
        "turns": [
            make_turn(
                turn_index=1,
                question="Analyse le burn-out selon la TRU.",
                intent="analysis",
                response=first_response,
            ),
            make_turn(
                turn_index=2,
                question="Quelles hypothèses fais-tu ?",
                intent="follow_up",
                response=second_response,
                is_follow_up=True,
                follow_up_intent="hypothesis_review",
            ),
        ],
    }

    context = ConversationContextBuilder().build(conversation)

    assert context.conversation_id == "conversation-burnout"
    assert context.turn_count == 2

    assert (
        context.current_question
        == "Quelles hypothèses fais-tu ?"
    )
    assert (
        context.previous_question
        == "Analyse le burn-out selon la TRU."
    )
    assert (
        context.last_independent_question
        == "Analyse le burn-out selon la TRU."
    )
    assert context.last_follow_up_intent == "hypothesis_review"

    assert context.main_subject == "burn-out"

    assert context.concepts == (
        "burn-out",
        "Delta",
        "reconnaissance",
    )

    assert context.explicit_claims == (
        "Le burn-out peut être étudié comme un processus d'épuisement.",
    )

    assert context.deductions == (
        "Un écart durable entre l'état vécu et l'état attendu "
        "peut renforcer la tension.",
    )

    assert context.hypotheses == (
        "Le Delta pourrait contribuer à modéliser cet écart.",
        "La répétition de l'écart pourrait participer à l'épuisement.",
    )

    assert context.unknowns == (
        "Le rôle causal exact du Delta reste à démontrer.",
    )

    assert context.missing_knowledge == (
        "Des données cliniques comparatives sont nécessaires.",
    )

    assert context.warnings == (
        "La TRU ne remplace pas un diagnostic médical.",
    )

    assert context.recent_questions == (
        "Analyse le burn-out selon la TRU.",
        "Quelles hypothèses fais-tu ?",
    )

    assert context.recent_summaries == (
        "Le burn-out est analysé comme une accumulation d'écarts "
        "non reconnus.",
        "Deux hypothèses principales relient le Delta "
        "à l'épuisement.",
    )

    assert context.request_ids == (
        "cognitive-request-burnout",
    )


def test_builder_removes_duplicate_values_without_changing_order():
    first_response = make_response(
        request_id="request-1",
        concepts=("Delta", "reconnaissance"),
        hypotheses=(
            "Le Delta représente un écart.",
        ),
        summary="Première réponse.",
    )

    second_response = make_response(
        request_id="request-2",
        concepts=("delta", "observation"),
        hypotheses=(
            "le delta représente un écart.",
            "L'observation rend l'écart perceptible.",
        ),
        summary="Deuxième réponse.",
    )

    conversation = {
        "conversation_id": "conversation-duplicates",
        "turns": [
            make_turn(
                turn_index=1,
                question="Explique Delta.",
                intent="explanation",
                response=first_response,
            ),
            make_turn(
                turn_index=2,
                question="Quel est le rôle de l'observation ?",
                intent="analysis",
                response=second_response,
            ),
        ],
    }

    context = ConversationContextBuilder().build(conversation)

    assert context.concepts == (
        "Delta",
        "reconnaissance",
        "observation",
    )

    assert context.hypotheses == (
        "Le Delta représente un écart.",
        "L'observation rend l'écart perceptible.",
    )

    assert context.request_ids == (
        "request-1",
        "request-2",
    )


def test_builder_limits_content_collection_to_recent_turns():
    turns = []

    for index in range(1, 6):
        response = make_response(
            request_id=f"request-{index}",
            concepts=(f"concept-{index}",),
            summary=f"Résumé {index}.",
        )

        turns.append(
            make_turn(
                turn_index=index,
                question=f"Question {index} ?",
                intent="analysis",
                response=response,
            )
        )

    conversation = {
        "conversation_id": "conversation-limit",
        "turn_count": 5,
        "turns": turns,
    }

    context = ConversationContextBuilder(
        recent_turn_limit=3
    ).build(conversation)

    assert context.turn_count == 5
    assert context.current_question == "Question 5 ?"
    assert context.previous_question == "Question 4 ?"

    assert context.recent_questions == (
        "Question 3 ?",
        "Question 4 ?",
        "Question 5 ?",
    )

    assert context.concepts == (
        "concept-3",
        "concept-4",
        "concept-5",
    )

    assert context.recent_summaries == (
        "Résumé 3.",
        "Résumé 4.",
        "Résumé 5.",
    )

    assert context.request_ids == (
        "request-3",
        "request-4",
        "request-5",
    )


def test_last_independent_question_can_precede_recent_turn_window():
    turns = [
        make_turn(
            turn_index=1,
            question="Analyse la reconnaissance selon la TRU.",
            intent="analysis",
            response=make_response(
                request_id="request-recognition",
                concepts=("reconnaissance",),
                summary="Analyse initiale.",
            ),
        ),
        make_turn(
            turn_index=2,
            question="Quelles hypothèses fais-tu ?",
            intent="follow_up",
            response=make_response(
                request_id="request-recognition",
                concepts=("reconnaissance",),
                summary="Hypothèses.",
            ),
            is_follow_up=True,
            follow_up_intent="hypothesis_review",
        ),
        make_turn(
            turn_index=3,
            question="Quelles preuves utilises-tu ?",
            intent="follow_up",
            response=make_response(
                request_id="request-recognition",
                concepts=("reconnaissance",),
                summary="Preuves.",
            ),
            is_follow_up=True,
            follow_up_intent="evidence_review",
        ),
    ]

    conversation = {
        "conversation_id": "conversation-independent-question",
        "turn_count": 3,
        "turns": turns,
    }

    context = ConversationContextBuilder(
        recent_turn_limit=2
    ).build(conversation)

    assert (
        context.last_independent_question
        == "Analyse la reconnaissance selon la TRU."
    )
    assert context.last_follow_up_intent == "evidence_review"

    assert context.recent_questions == (
        "Quelles hypothèses fais-tu ?",
        "Quelles preuves utilises-tu ?",
    )


def test_main_subject_falls_back_to_independent_question():
    conversation = {
        "conversation_id": "conversation-without-concepts",
        "turn_count": 2,
        "turns": [
            make_turn(
                turn_index=1,
                question="Analyse la chute de Constantinople.",
                intent="analysis",
                response=make_response(
                    request_id="request-constantinople",
                    summary="Analyse historique.",
                ),
            ),
            make_turn(
                turn_index=2,
                question="Quelles hypothèses fais-tu ?",
                intent="follow_up",
                response=make_response(
                    request_id="request-constantinople",
                    summary="Hypothèses historiques.",
                ),
                is_follow_up=True,
                follow_up_intent="hypothesis_review",
            ),
        ],
    }

    context = ConversationContextBuilder().build(conversation)

    assert (
        context.main_subject
        == "Analyse la chute de Constantinople."
    )


def test_builder_supports_response_stored_directly_in_turn():
    conversation = {
        "conversation_id": "conversation-direct-response",
        "turns": [
            {
                "question": "Explique la reconnaissance.",
                "intent": "explanation",
                "is_follow_up": False,
                "request_id": "request-direct",
                "answer": {
                    "summary": "La reconnaissance rend un état perceptible.",
                },
                "classifications": {
                    "EXPLICITE": [
                        {
                            "text": (
                                "La reconnaissance suppose une relation "
                                "entre un état et son observation."
                            )
                        }
                    ],
                    "DÉDUCTION": [],
                    "HYPOTHÈSE": [],
                    "INCONNU": [],
                },
                "execution": {
                    "concepts_recognized": [
                        "reconnaissance",
                    ],
                    "final_answer": (
                        "La reconnaissance rend un état perceptible."
                    ),
                },
            }
        ],
    }

    context = ConversationContextBuilder().build(conversation)

    assert context.main_subject == "reconnaissance"
    assert context.current_question == "Explique la reconnaissance."

    assert context.explicit_claims == (
        "La reconnaissance suppose une relation "
        "entre un état et son observation.",
    )

    assert context.recent_summaries == (
        "La reconnaissance rend un état perceptible.",
    )

    assert context.request_ids == (
        "request-direct",
    )


def test_context_can_be_serialized_to_dictionary():
    context = ConversationContextBuilder.empty(
        conversation_id="conversation-serialization"
    )

    payload = context.to_dict()

    assert payload["conversation_id"] == (
        "conversation-serialization"
    )
    assert payload["turn_count"] == 0
    assert payload["concepts"] == ()
    assert payload["recent_questions"] == ()