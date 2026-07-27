from __future__ import annotations

from tru_ai.cognitive.conversation.context_builder import (
    ConversationContext,
)
from tru_ai.cognitive.conversation.question_rewriter import (
    QuestionRewriter,
    RewrittenQuestion,
)
from tru_ai.cognitive.conversation.reference_resolver import (
    ReferenceResolver,
    ReferenceType,
)


def make_context(
    *,
    main_subject: str | None = "burn-out",
    current_question: str | None = "Quelles hypothèses fais-tu ?",
    previous_question: str | None = (
        "Analyse le burn-out selon la TRU."
    ),
    last_independent_question: str | None = (
        "Analyse le burn-out selon la TRU."
    ),
    concepts: tuple[str, ...] = (
        "burn-out",
        "Delta",
        "reconnaissance",
    ),
    explicit_claims: tuple[str, ...] = (
        "Le burn-out est un état d'épuisement professionnel.",
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
    ),
    missing_knowledge: tuple[str, ...] = (
        "Des données cliniques comparatives sont nécessaires.",
    ),
    warnings: tuple[str, ...] = (
        "La TRU ne remplace pas un diagnostic médical.",
    ),
    recent_summaries: tuple[str, ...] = (
        "Le burn-out peut être analysé comme un écart durable.",
        "Trois hypothèses relient le Delta à l'épuisement.",
    ),
) -> ConversationContext:
    return ConversationContext(
        conversation_id="conversation-question-rewriter",
        turn_count=3,
        main_subject=main_subject,
        current_question=current_question,
        previous_question=previous_question,
        last_independent_question=last_independent_question,
        last_follow_up_intent="follow_up",
        concepts=concepts,
        explicit_claims=explicit_claims,
        deductions=deductions,
        hypotheses=hypotheses,
        unknowns=unknowns,
        missing_knowledge=missing_knowledge,
        warnings=warnings,
        recent_questions=(
            "Analyse le burn-out selon la TRU.",
            "Quelles hypothèses fais-tu ?",
        ),
        recent_summaries=recent_summaries,
        request_ids=(
            "request-1",
            "request-2",
        ),
    )


def rewrite(
    question: str,
    context: ConversationContext | None = None,
) -> RewrittenQuestion:
    actual_context = context or make_context()

    resolution = ReferenceResolver().resolve(
        question=question,
        context=actual_context,
    )

    return QuestionRewriter().rewrite(
        question=question,
        context=actual_context,
        resolution=resolution,
    )


def test_empty_question_is_not_rewritten():
    result = rewrite("   ")

    assert result.original_question == ""
    assert result.rewritten_question == ""
    assert result.was_rewritten is False
    assert result.rewrite_reason is None
    assert result.references_used == ()
    assert result.warnings == ()


def test_autonomous_question_is_preserved():
    result = rewrite(
        "Quelle est la définition générale de la conscience ?",
        make_context(concepts=()),
    )

    assert result.rewritten_question == (
        "Quelle est la définition générale de la conscience ?"
    )
    assert result.was_rewritten is False
    assert result.rewrite_reason is None


def test_rewrites_second_hypothesis():
    result = rewrite(
        "Développe la deuxième hypothèse."
    )

    assert result.rewritten_question == (
        "Développe l'hypothèse suivant : "
        "« La répétition de l'écart pourrait produire "
        "un épuisement. »"
    )

    assert result.was_rewritten is True
    assert result.rewrite_reason == (
        "resolved_category_reference"
    )

    assert len(result.references_used) == 1
    assert result.references_used[0].reference_type == (
        ReferenceType.HYPOTHESIS
    )
    assert result.references_used[0].source_index == 2


def test_rewrites_deduction_reference():
    result = rewrite(
        "Justifie la deuxième déduction."
    )

    assert result.rewritten_question == (
        "Justifie la déduction suivant : "
        "« La non-reconnaissance peut prolonger l'écart. »"
    )


def test_rewrites_explicit_claim_reference():
    result = rewrite(
        "Explique cette affirmation."
    )

    assert result.rewritten_question == (
        "Explique l'affirmation suivant : "
        "« Le burn-out est un état d'épuisement professionnel. »"
    )


def test_rewrites_unknown_reference():
    result = rewrite(
        "Développe cette inconnue."
    )

    assert result.rewritten_question == (
        "Développe l'inconnue suivant : "
        "« Le rôle causal exact du Delta reste à démontrer. »"
    )


def test_rewrites_missing_knowledge_reference():
    result = rewrite(
        "Explique cette connaissance manquante."
    )

    assert result.rewritten_question == (
        "Explique la connaissance manquante suivant : "
        "« Des données cliniques comparatives sont nécessaires. »"
    )


def test_rewrites_warning_reference():
    result = rewrite(
        "Développe cet avertissement."
    )

    assert result.rewritten_question == (
        "Développe l'avertissement suivant : "
        "« La TRU ne remplace pas un diagnostic médical. »"
    )


def test_rewrites_all_hypotheses():
    result = rewrite(
        "Énumère les hypothèses."
    )

    assert result.rewritten_question == (
        "Énumère les hypothèses suivants :\n"
        "1. « Le Delta pourrait modéliser l'écart. »\n"
        "2. « La répétition de l'écart pourrait produire "
        "un épuisement. »\n"
        "3. « La reconnaissance pourrait interrompre "
        "la répétition. »"
    )


def test_short_why_question_uses_previous_answer():
    result = rewrite("Pourquoi ?")

    assert result.rewritten_question == (
        "Explique pourquoi le contenu de la réponse précédente : "
        "« Trois hypothèses relient le Delta à l'épuisement. »"
    )

    assert result.rewrite_reason == (
        "resolved_implicit_reference"
    )


def test_short_develop_question_uses_previous_answer():
    result = rewrite("Développe.")

    assert result.rewritten_question == (
        "Développe le contenu de la réponse précédente : "
        "« Trois hypothèses relient le Delta à l'épuisement. »"
    )


def test_generic_hypothesis_reference_is_expanded():
    result = rewrite("Pourquoi cela ?")

    assert result.rewritten_question == (
        "Explique pourquoi l'hypothèse suivant : "
        "« La reconnaissance pourrait interrompre "
        "la répétition. »"
    )


def test_generic_previous_answer_reference_is_expanded():
    result = rewrite("Explique cette réponse.")

    assert result.rewritten_question == (
        "Explique le contenu de la réponse précédente : "
        "« Trois hypothèses relient le Delta à l'épuisement. »"
    )


def test_comparative_target_uses_previous_summary():
    result = rewrite(
        "Et pour la dépression ?"
    )

    assert result.rewritten_question == (
        "Applique à dépression le même raisonnement que celui "
        "présenté précédemment : "
        "« Trois hypothèses relient le Delta à l'épuisement. »"
    )

    assert result.comparative_target == "dépression"
    assert result.carry_previous_reasoning is True
    assert result.rewrite_reason == "comparative_target"


def test_comparative_target_falls_back_to_previous_question():
    context = make_context(
        recent_summaries=(),
        deductions=(),
        hypotheses=(),
    )

    result = rewrite(
        "Et pour la dépression ?",
        context,
    )

    assert result.rewritten_question == (
        "Analyse dépression en reprenant la méthode utilisée "
        "pour répondre à la question précédente : "
        "« Analyse le burn-out selon la TRU. »"
    )


def test_comparative_target_falls_back_to_main_subject():
    context = make_context(
        recent_summaries=(),
        deductions=(),
        hypotheses=(),
        previous_question=None,
        last_independent_question=None,
    )

    result = rewrite(
        "Et pour la dépression ?",
        context,
    )

    assert result.rewritten_question == (
        "Compare dépression avec le sujet précédemment étudié, "
        "« burn-out », en conservant le même cadre d'analyse."
    )


def test_explicit_concept_question_is_preserved():
    result = rewrite(
        "Parle davantage du Delta."
    )

    assert result.rewritten_question == (
        "Parle davantage du Delta."
    )
    assert result.was_rewritten is False


def test_multiple_concepts_are_preserved_when_explicit():
    context = make_context(
        concepts=(
            "Delta",
            "reconnaissance",
        )
    )

    result = rewrite(
        "Compare Delta et reconnaissance.",
        context,
    )

    assert result.rewritten_question == (
        "Compare Delta et reconnaissance."
    )


def test_category_and_concept_reference_prefers_category_rewrite():
    result = rewrite(
        "Explique la deuxième hypothèse sur le Delta."
    )

    assert result.rewritten_question == (
        "Explique l'hypothèse suivant : "
        "« La répétition de l'écart pourrait produire "
        "un épuisement. »"
    )


def test_unresolved_reference_adds_warning():
    context = make_context(
        hypotheses=(),
    )

    result = rewrite(
        "Explique cette hypothèse.",
        context,
    )

    assert result.was_rewritten is True

    assert (
        "Référence non résolue : hypothese"
        in result.warnings
    )

    assert "n'ont pas pu être résolues" in (
        result.rewritten_question
    )


def test_contextual_question_without_resolution_adds_warning():
    context = make_context(
        main_subject=None,
        previous_question=None,
        last_independent_question=None,
        recent_summaries=(),
        deductions=(),
        hypotheses=(),
        explicit_claims=(),
    )

    result = rewrite(
        "Pourquoi ?",
        context,
    )

    assert result.rewritten_question == "Pourquoi ?"
    assert result.was_rewritten is False

    assert result.warnings == (
        "La question dépend du contexte, mais aucune référence "
        "précise n'a été résolue.",
    )


def test_previous_question_fallback():
    context = make_context(
        recent_summaries=(),
        hypotheses=(),
        deductions=(),
        explicit_claims=(),
    )

    result = rewrite(
        "Pourquoi cela ?",
        context,
    )

    assert result.rewritten_question == (
        "Explique pourquoi la question précédente : "
        "« Analyse le burn-out selon la TRU. »"
    )


def test_rewritten_question_serialization():
    result = rewrite(
        "Développe la deuxième hypothèse."
    )

    payload = result.to_dict()

    assert payload["original_question"] == (
        "Développe la deuxième hypothèse."
    )
    assert payload["rewritten_question"] == (
        "Développe l'hypothèse suivant : "
        "« La répétition de l'écart pourrait produire "
        "un épuisement. »"
    )
    assert payload["was_rewritten"] is True
    assert payload["rewrite_reason"] == (
        "resolved_category_reference"
    )
    assert payload["comparative_target"] is None
    assert payload["carry_previous_reasoning"] is False
    assert payload["warnings"] == []

    assert payload["references_used"][0][
        "reference_type"
    ] == "hypothesis"


def test_rewriting_is_deterministic():
    context = make_context()
    resolver = ReferenceResolver()
    rewriter = QuestionRewriter()

    resolution = resolver.resolve(
        question="Développe la deuxième hypothèse.",
        context=context,
    )

    first = rewriter.rewrite(
        question="Développe la deuxième hypothèse.",
        context=context,
        resolution=resolution,
    )

    second = rewriter.rewrite(
        question="Développe la deuxième hypothèse.",
        context=context,
        resolution=resolution,
    )

    assert first == second
    assert first.to_dict() == second.to_dict()