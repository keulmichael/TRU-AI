from __future__ import annotations

import pytest

from tru_ai.cognitive.conversation.context_builder import (
    ConversationContext,
)
from tru_ai.cognitive.conversation.reference_resolver import (
    ReferenceResolution,
    ReferenceResolver,
    ReferenceType,
    ResolvedReference,
)


def make_context(
    *,
    conversation_id: str = "conversation-reference-test",
    turn_count: int = 3,
    main_subject: str | None = "burn-out",
    current_question: str | None = "Quelles hypothèses fais-tu ?",
    previous_question: str | None = "Analyse le burn-out selon la TRU.",
    last_independent_question: str | None = (
        "Analyse le burn-out selon la TRU."
    ),
    last_follow_up_intent: str | None = "hypothesis_review",
    concepts: tuple[str, ...] = (
        "burn-out",
        "Delta",
        "reconnaissance",
    ),
    explicit_claims: tuple[str, ...] = (
        "Le burn-out est un état d'épuisement professionnel.",
        "La reconnaissance suppose l'observation d'un état.",
    ),
    deductions: tuple[str, ...] = (
        "Un écart durable peut renforcer la tension.",
        "La non-reconnaissance peut prolonger l'écart.",
    ),
    hypotheses: tuple[str, ...] = (
        "Le Delta pourrait modéliser l'écart.",
        "La répétition de l'écart pourrait produire un épuisement.",
        "La reconnaissance pourrait interrompre la répétition.",
    ),
    unknowns: tuple[str, ...] = (
        "Le rôle causal exact du Delta reste à démontrer.",
        "La portée clinique du modèle reste inconnue.",
    ),
    missing_knowledge: tuple[str, ...] = (
        "Des données cliniques comparatives sont nécessaires.",
        "Un protocole expérimental doit encore être défini.",
    ),
    warnings: tuple[str, ...] = (
        "La TRU ne remplace pas un diagnostic médical.",
        "Les hypothèses doivent rester distinguées des faits.",
    ),
    recent_questions: tuple[str, ...] = (
        "Analyse le burn-out selon la TRU.",
        "Quelles hypothèses fais-tu ?",
    ),
    recent_summaries: tuple[str, ...] = (
        "Le burn-out peut être analysé comme un écart durable.",
        "Trois hypothèses relient le Delta à l'épuisement.",
    ),
    request_ids: tuple[str, ...] = (
        "request-1",
        "request-2",
    ),
) -> ConversationContext:
    return ConversationContext(
        conversation_id=conversation_id,
        turn_count=turn_count,
        main_subject=main_subject,
        current_question=current_question,
        previous_question=previous_question,
        last_independent_question=last_independent_question,
        last_follow_up_intent=last_follow_up_intent,
        concepts=concepts,
        explicit_claims=explicit_claims,
        deductions=deductions,
        hypotheses=hypotheses,
        unknowns=unknowns,
        missing_knowledge=missing_knowledge,
        warnings=warnings,
        recent_questions=recent_questions,
        recent_summaries=recent_summaries,
        request_ids=request_ids,
    )


def test_empty_question_returns_empty_resolution():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="   ",
        context=make_context(),
    )

    assert isinstance(resolution, ReferenceResolution)
    assert resolution.original_question == ""
    assert resolution.normalized_question == ""
    assert resolution.references == ()
    assert resolution.unresolved_expressions == ()
    assert resolution.requires_context is False
    assert resolution.comparative_target is None
    assert resolution.carry_previous_reasoning is False
    assert resolution.has_references is False
    assert resolution.primary_reference is None


def test_resolves_first_hypothesis_by_ordinal_word():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe la première hypothèse.",
        context=make_context(),
    )

    assert resolution.has_references is True
    assert resolution.requires_context is True

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 1

    reference = hypothesis_references[0]

    assert reference.reference_type == ReferenceType.HYPOTHESIS
    assert reference.value == "Le Delta pourrait modéliser l'écart."
    assert reference.source_index == 1
    assert reference.confidence == pytest.approx(0.99)


def test_resolves_second_hypothesis_by_ordinal_word():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe la deuxième hypothèse.",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 1

    reference = hypothesis_references[0]

    assert reference.value == (
        "La répétition de l'écart pourrait produire un épuisement."
    )
    assert reference.source_index == 2
    assert reference.confidence == pytest.approx(0.99)


def test_resolves_third_hypothesis_with_unaccented_question():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique la troisieme hypothese.",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 1

    reference = hypothesis_references[0]

    assert reference.value == (
        "La reconnaissance pourrait interrompre la répétition."
    )
    assert reference.source_index == 3


def test_resolves_hypothesis_by_numeric_index():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe l'hypothèse numéro 2.",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 1
    assert hypothesis_references[0].source_index == 2
    assert hypothesis_references[0].value == (
        "La répétition de l'écart pourrait produire un épuisement."
    )


def test_unavailable_hypothesis_index_is_reported_as_unresolved():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe la cinquième hypothèse.",
        context=make_context(),
    )

    assert resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    ) == ()

    assert resolution.unresolved_expressions == (
        "cinquième hypothese",
    )

    assert resolution.requires_context is True


def test_resolves_all_hypotheses_for_plural_request():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Quelles sont les hypothèses ?",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 3

    assert tuple(
        reference.source_index
        for reference in hypothesis_references
    ) == (
        1,
        2,
        3,
    )

    assert tuple(
        reference.value
        for reference in hypothesis_references
    ) == make_context().hypotheses


def test_resolves_last_hypothesis_without_ordinal():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique cette hypothèse.",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 1

    reference = hypothesis_references[0]

    assert reference.value == (
        "La reconnaissance pourrait interrompre la répétition."
    )
    assert reference.source_index == 3
    assert reference.confidence == pytest.approx(0.88)


def test_resolves_second_deduction():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Justifie la deuxième déduction.",
        context=make_context(),
    )

    deduction_references = resolution.references_of_type(
        ReferenceType.DEDUCTION
    )

    assert len(deduction_references) == 1

    reference = deduction_references[0]

    assert reference.value == (
        "La non-reconnaissance peut prolonger l'écart."
    )
    assert reference.source_index == 2


def test_resolves_all_deductions():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Énumère les déductions.",
        context=make_context(),
    )

    deduction_references = resolution.references_of_type(
        ReferenceType.DEDUCTION
    )

    assert len(deduction_references) == 2

    assert tuple(
        reference.value
        for reference in deduction_references
    ) == make_context().deductions


def test_resolves_explicit_claim_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique la première affirmation.",
        context=make_context(),
    )

    explicit_references = resolution.references_of_type(
        ReferenceType.EXPLICIT_CLAIM
    )

    assert len(explicit_references) == 1

    assert explicit_references[0].value == (
        "Le burn-out est un état d'épuisement professionnel."
    )
    assert explicit_references[0].source_index == 1


def test_resolves_unknown_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe le deuxième inconnu.",
        context=make_context(),
    )

    unknown_references = resolution.references_of_type(
        ReferenceType.UNKNOWN
    )

    assert len(unknown_references) == 1

    assert unknown_references[0].value == (
        "La portée clinique du modèle reste inconnue."
    )
    assert unknown_references[0].source_index == 2


def test_resolves_missing_knowledge_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique la première connaissance manquante.",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.MISSING_KNOWLEDGE
    )

    assert len(references) == 1

    assert references[0].value == (
        "Des données cliniques comparatives sont nécessaires."
    )
    assert references[0].source_index == 1


def test_resolves_warning_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe le deuxième avertissement.",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.WARNING
    )

    assert len(references) == 1

    assert references[0].value == (
        "Les hypothèses doivent rester distinguées des faits."
    )
    assert references[0].source_index == 2


def test_resolves_summary_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique le premier résumé.",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.SUMMARY
    )

    assert len(references) == 1

    assert references[0].value == (
        "Le burn-out peut être analysé comme un écart durable."
    )
    assert references[0].source_index == 1


def test_resolves_explicit_concept_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Parle davantage du Delta.",
        context=make_context(),
    )

    concept_references = resolution.references_of_type(
        ReferenceType.CONCEPT
    )

    assert len(concept_references) == 1

    reference = concept_references[0]

    assert reference.value == "Delta"
    assert reference.source_index == 2
    assert reference.matched_expression == "Delta"
    assert reference.confidence == pytest.approx(0.97)


def test_concept_resolution_is_case_insensitive():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Quel est le rôle de la RECONNAISSANCE ?",
        context=make_context(),
    )

    concept_references = resolution.references_of_type(
        ReferenceType.CONCEPT
    )

    assert len(concept_references) == 1
    assert concept_references[0].value == "reconnaissance"


def test_concept_resolution_is_accent_insensitive():
    resolver = ReferenceResolver()

    context = make_context(
        concepts=(
            "réflexivité",
            "reconnaissance",
        )
    )

    resolution = resolver.resolve(
        question="Explique la reflexivite.",
        context=context,
    )

    concept_references = resolution.references_of_type(
        ReferenceType.CONCEPT
    )

    assert len(concept_references) == 1
    assert concept_references[0].value == "réflexivité"


def test_concept_matching_does_not_match_inside_another_word():
    resolver = ReferenceResolver()

    context = make_context(
        concepts=(
            "âme",
        )
    )

    resolution = resolver.resolve(
        question="Analyse la trame de cette théorie.",
        context=context,
    )

    assert resolution.references_of_type(
        ReferenceType.CONCEPT
    ) == ()


def test_generic_previous_answer_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique cette réponse.",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_ANSWER
    )

    assert len(references) == 1

    reference = references[0]

    assert reference.value == (
        "Trois hypothèses relient le Delta à l'épuisement."
    )
    assert reference.source_index == 2
    assert reference.confidence == pytest.approx(0.93)


def test_generic_previous_reasoning_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe le raisonnement précédent.",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_ANSWER
    )

    assert len(references) == 1
    assert references[0].value == (
        "Trois hypothèses relient le Delta à l'épuisement."
    )


def test_generic_reference_prefers_latest_hypothesis():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Pourquoi cela ?",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(hypothesis_references) == 1

    reference = hypothesis_references[0]

    assert reference.value == (
        "La reconnaissance pourrait interrompre la répétition."
    )
    assert reference.source_index == 3


def test_generic_reference_falls_back_to_latest_deduction():
    resolver = ReferenceResolver()

    context = make_context(
        hypotheses=(),
    )

    resolution = resolver.resolve(
        question="Pourquoi cela ?",
        context=context,
    )

    deduction_references = resolution.references_of_type(
        ReferenceType.DEDUCTION
    )

    assert len(deduction_references) == 1
    assert deduction_references[0].value == (
        "La non-reconnaissance peut prolonger l'écart."
    )


def test_generic_reference_falls_back_to_explicit_claim():
    resolver = ReferenceResolver()

    context = make_context(
        hypotheses=(),
        deductions=(),
    )

    resolution = resolver.resolve(
        question="Explique ce point.",
        context=context,
    )

    explicit_references = resolution.references_of_type(
        ReferenceType.EXPLICIT_CLAIM
    )

    assert len(explicit_references) == 1
    assert explicit_references[0].value == (
        "La reconnaissance suppose l'observation d'un état."
    )


def test_generic_reference_falls_back_to_previous_summary():
    resolver = ReferenceResolver()

    context = make_context(
        hypotheses=(),
        deductions=(),
        explicit_claims=(),
    )

    resolution = resolver.resolve(
        question="Pourquoi cela ?",
        context=context,
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_ANSWER
    )

    assert len(references) == 1
    assert references[0].value == (
        "Trois hypothèses relient le Delta à l'épuisement."
    )


def test_generic_reference_falls_back_to_previous_question():
    resolver = ReferenceResolver()

    context = make_context(
        hypotheses=(),
        deductions=(),
        explicit_claims=(),
        recent_summaries=(),
    )

    resolution = resolver.resolve(
        question="Pourquoi cela ?",
        context=context,
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_QUESTION
    )

    assert len(references) == 1
    assert references[0].value == (
        "Analyse le burn-out selon la TRU."
    )


def test_generic_reference_falls_back_to_main_subject():
    resolver = ReferenceResolver()

    context = make_context(
        hypotheses=(),
        deductions=(),
        explicit_claims=(),
        recent_summaries=(),
        previous_question=None,
        last_independent_question=None,
    )

    resolution = resolver.resolve(
        question="Explique cela.",
        context=context,
    )

    references = resolution.references_of_type(
        ReferenceType.MAIN_SUBJECT
    )

    assert len(references) == 1
    assert references[0].value == "burn-out"


def test_short_why_question_targets_previous_answer():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Pourquoi ?",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_ANSWER
    )

    assert len(references) == 1

    assert references[0].value == (
        "Trois hypothèses relient le Delta à l'épuisement."
    )

    assert resolution.requires_context is True


def test_short_how_question_targets_previous_answer():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Comment ?",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_ANSWER
    )

    assert len(references) == 1
    assert references[0].source_index == 2


def test_short_develop_request_targets_previous_answer():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe.",
        context=make_context(),
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_ANSWER
    )

    assert len(references) == 1


def test_short_contextual_question_falls_back_to_previous_question():
    resolver = ReferenceResolver()

    context = make_context(
        recent_summaries=(),
    )

    resolution = resolver.resolve(
        question="Pourquoi ?",
        context=context,
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_QUESTION
    )

    assert len(references) == 1
    assert references[0].value == (
        "Analyse le burn-out selon la TRU."
    )


def test_short_contextual_question_falls_back_to_independent_question():
    resolver = ReferenceResolver()

    context = make_context(
        recent_summaries=(),
        previous_question=None,
    )

    resolution = resolver.resolve(
        question="Explique.",
        context=context,
    )

    references = resolution.references_of_type(
        ReferenceType.PREVIOUS_QUESTION
    )

    assert len(references) == 1
    assert references[0].value == (
        "Analyse le burn-out selon la TRU."
    )


def test_comparative_target_with_et_pour():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Et pour la dépression ?",
        context=make_context(),
    )

    assert resolution.comparative_target == "dépression"
    assert resolution.carry_previous_reasoning is True
    assert resolution.requires_context is True

    comparative_references = resolution.references_of_type(
        ReferenceType.COMPARATIVE_TARGET
    )

    assert len(comparative_references) == 1

    reference = comparative_references[0]

    assert reference.value == "dépression"
    assert reference.source_index is None
    assert reference.confidence == pytest.approx(0.98)


def test_comparative_target_without_et():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Pour le burn-out ?",
        context=make_context(),
    )

    assert resolution.comparative_target == "burn-out"
    assert resolution.carry_previous_reasoning is True


def test_comparative_target_with_qu_en_est_il():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Et qu'en est-il de la dépression ?",
        context=make_context(),
    )

    assert resolution.comparative_target == "dépression"
    assert resolution.carry_previous_reasoning is True


def test_comparative_target_with_case_expression():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Dans le cas du burn-out ?",
        context=make_context(),
    )

    assert resolution.comparative_target == "burn-out"
    assert resolution.carry_previous_reasoning is True


def test_comparative_target_with_apply_expression():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Applique ce raisonnement à la dépression.",
        context=make_context(),
    )

    assert resolution.comparative_target == "dépression"
    assert resolution.carry_previous_reasoning is True


def test_comparative_target_removes_leading_article():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Et pour une dépression chronique ?",
        context=make_context(),
    )

    assert resolution.comparative_target == (
        "dépression chronique"
    )


def test_explicit_concept_and_category_can_both_be_resolved():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique la deuxième hypothèse sur le Delta.",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    concept_references = resolution.references_of_type(
        ReferenceType.CONCEPT
    )

    assert len(hypothesis_references) == 1
    assert hypothesis_references[0].source_index == 2

    assert len(concept_references) == 1
    assert concept_references[0].value == "Delta"


def test_explicit_reference_prevents_generic_duplicate_resolution():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique cette hypothèse.",
        context=make_context(),
    )

    assert len(resolution.references) == 1
    assert (
        resolution.references[0].reference_type
        == ReferenceType.HYPOTHESIS
    )


def test_unavailable_category_is_marked_unresolved():
    resolver = ReferenceResolver()

    context = make_context(
        hypotheses=(),
    )

    resolution = resolver.resolve(
        question="Explique cette hypothèse.",
        context=context,
    )

    assert resolution.references == ()
    assert resolution.unresolved_expressions == (
        "hypothese",
    )
    assert resolution.requires_context is True


def test_plural_category_without_values_is_marked_unresolved():
    resolver = ReferenceResolver()

    context = make_context(
        deductions=(),
    )

    resolution = resolver.resolve(
        question="Énumère les déductions.",
        context=context,
    )

    assert resolution.references == ()
    assert resolution.unresolved_expressions == (
        "deductions",
    )
    assert resolution.requires_context is True


def test_autonomous_question_without_reference_does_not_require_context():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question=(
            "Quelle est la définition générale de la "
            "réflexivité universelle ?"
        ),
        context=make_context(
            concepts=(),
        ),
    )

    assert resolution.references == ()
    assert resolution.unresolved_expressions == ()
    assert resolution.requires_context is False
    assert resolution.comparative_target is None
    assert resolution.carry_previous_reasoning is False


def test_long_question_starting_with_pourquoi_is_not_automatically_contextual():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question=(
            "Pourquoi la reconnaissance joue-t-elle un rôle "
            "central dans la TRU ?"
        ),
        context=make_context(
            concepts=(),
        ),
    )

    assert resolution.references == ()
    assert resolution.requires_context is False


def test_primary_reference_returns_highest_confidence_reference():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique la deuxième hypothèse sur le Delta.",
        context=make_context(),
    )

    primary_reference = resolution.primary_reference

    assert primary_reference is not None
    assert primary_reference.reference_type == (
        ReferenceType.HYPOTHESIS
    )
    assert primary_reference.source_index == 2
    assert primary_reference.confidence == pytest.approx(0.99)


def test_references_of_type_returns_only_requested_type():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Explique la première hypothèse sur le Delta.",
        context=make_context(),
    )

    hypothesis_references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    concept_references = resolution.references_of_type(
        ReferenceType.CONCEPT
    )

    warning_references = resolution.references_of_type(
        ReferenceType.WARNING
    )

    assert len(hypothesis_references) == 1
    assert len(concept_references) == 1
    assert warning_references == ()


def test_resolved_reference_serialization():
    reference = ResolvedReference(
        reference_type=ReferenceType.HYPOTHESIS,
        value="Le Delta pourrait modéliser l'écart.",
        source_index=1,
        matched_expression="première hypothèse",
        confidence=0.99,
    )

    payload = reference.to_dict()

    assert payload == {
        "reference_type": "hypothesis",
        "value": "Le Delta pourrait modéliser l'écart.",
        "source_index": 1,
        "matched_expression": "première hypothèse",
        "confidence": 0.99,
    }


def test_reference_resolution_serialization():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="Développe la deuxième hypothèse.",
        context=make_context(),
    )

    payload = resolution.to_dict()

    assert payload["original_question"] == (
        "Développe la deuxième hypothèse."
    )
    assert payload["normalized_question"] == (
        "developpe la deuxieme hypothese."
    )
    assert payload["requires_context"] is True
    assert payload["comparative_target"] is None
    assert payload["carry_previous_reasoning"] is False
    assert payload["has_references"] is True

    assert len(payload["references"]) == 1

    assert payload["references"][0]["reference_type"] == (
        "hypothesis"
    )
    assert payload["references"][0]["source_index"] == 2

    assert payload["primary_reference"]["reference_type"] == (
        "hypothesis"
    )


def test_resolution_removes_duplicate_references():
    resolver = ReferenceResolver()

    context = make_context(
        concepts=(
            "Delta",
            "delta",
        )
    )

    resolution = resolver.resolve(
        question="Explique Delta.",
        context=context,
    )

    concept_references = resolution.references_of_type(
        ReferenceType.CONCEPT
    )

    assert len(concept_references) == 2

    assert concept_references[0].value == "Delta"
    assert concept_references[0].source_index == 1

    assert concept_references[1].value == "delta"
    assert concept_references[1].source_index == 2


def test_question_text_is_cleaned_before_resolution():
    resolver = ReferenceResolver()

    resolution = resolver.resolve(
        question="   Développe    la deuxième    hypothèse.   ",
        context=make_context(),
    )

    assert resolution.original_question == (
        "Développe la deuxième hypothèse."
    )

    assert resolution.normalized_question == (
        "developpe la deuxieme hypothese."
    )

    references = resolution.references_of_type(
        ReferenceType.HYPOTHESIS
    )

    assert len(references) == 1
    assert references[0].source_index == 2


def test_reference_resolution_is_deterministic():
    resolver = ReferenceResolver()
    context = make_context()

    first_resolution = resolver.resolve(
        question="Explique la deuxième hypothèse sur le Delta.",
        context=context,
    )

    second_resolution = resolver.resolve(
        question="Explique la deuxième hypothèse sur le Delta.",
        context=context,
    )

    assert first_resolution == second_resolution
    assert first_resolution.to_dict() == second_resolution.to_dict()


def test_empty_context_cannot_resolve_short_reference():
    resolver = ReferenceResolver()

    context = make_context(
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
        turn_count=0,
    )

    resolution = resolver.resolve(
        question="Pourquoi ?",
        context=context,
    )

    assert resolution.references == ()
    assert resolution.unresolved_expressions == ()
    assert resolution.requires_context is True
    assert resolution.primary_reference is None