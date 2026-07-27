from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from tru_ai.cognitive.conversation.context_builder import (
    ConversationContext,
)
from tru_ai.cognitive.conversation.reference_resolver import (
    ReferenceResolution,
    ReferenceType,
    ResolvedReference,
)


@dataclass(frozen=True)
class RewrittenQuestion:
    """
    Résultat de la réécriture conversationnelle.

    La question réécrite doit pouvoir être comprise sans accès direct
    à l'historique de la conversation.
    """

    original_question: str
    rewritten_question: str
    was_rewritten: bool
    rewrite_reason: str | None
    references_used: tuple[ResolvedReference, ...]
    comparative_target: str | None
    carry_previous_reasoning: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "original_question": self.original_question,
            "rewritten_question": self.rewritten_question,
            "was_rewritten": self.was_rewritten,
            "rewrite_reason": self.rewrite_reason,
            "references_used": [
                reference.to_dict()
                for reference in self.references_used
            ],
            "comparative_target": self.comparative_target,
            "carry_previous_reasoning": self.carry_previous_reasoning,
            "warnings": list(self.warnings),
        }


class QuestionRewriter:
    """
    Réécrit une question conversationnelle en question autonome.

    Le composant :

    - conserve les questions déjà autonomes ;
    - remplace les références implicites par leur contenu résolu ;
    - transporte le raisonnement précédent vers une nouvelle cible ;
    - n'invente aucune information ;
    - signale les références qui n'ont pas pu être résolues.
    """

    def rewrite(
        self,
        *,
        question: str,
        context: ConversationContext,
        resolution: ReferenceResolution,
    ) -> RewrittenQuestion:
        original_question = self._clean_text(question)

        if not original_question:
            return RewrittenQuestion(
                original_question="",
                rewritten_question="",
                was_rewritten=False,
                rewrite_reason=None,
                references_used=(),
                comparative_target=None,
                carry_previous_reasoning=False,
                warnings=(),
            )

        warnings = self._build_warnings(resolution)

        if not resolution.requires_context:
            return RewrittenQuestion(
                original_question=original_question,
                rewritten_question=original_question,
                was_rewritten=False,
                rewrite_reason=None,
                references_used=(),
                comparative_target=None,
                carry_previous_reasoning=False,
                warnings=warnings,
            )

        if resolution.comparative_target:
            rewritten = self._rewrite_comparative_question(
                target=resolution.comparative_target,
                context=context,
                resolution=resolution,
            )

            return RewrittenQuestion(
                original_question=original_question,
                rewritten_question=rewritten,
                was_rewritten=rewritten != original_question,
                rewrite_reason="comparative_target",
                references_used=resolution.references,
                comparative_target=resolution.comparative_target,
                carry_previous_reasoning=True,
                warnings=warnings,
            )

        category_rewrite = self._rewrite_category_reference(
            original_question=original_question,
            references=resolution.references,
        )

        if category_rewrite:
            return RewrittenQuestion(
                original_question=original_question,
                rewritten_question=category_rewrite,
                was_rewritten=category_rewrite != original_question,
                rewrite_reason="resolved_category_reference",
                references_used=resolution.references,
                comparative_target=None,
                carry_previous_reasoning=False,
                warnings=warnings,
            )

        concept_rewrite = self._rewrite_concept_reference(
            original_question=original_question,
            references=resolution.references,
        )

        if concept_rewrite:
            return RewrittenQuestion(
                original_question=original_question,
                rewritten_question=concept_rewrite,
                was_rewritten=concept_rewrite != original_question,
                rewrite_reason=(
                    "resolved_concept_reference"
                    if concept_rewrite != original_question
                    else None
                ),
                references_used=resolution.references,
                comparative_target=None,
                carry_previous_reasoning=False,
                warnings=warnings,
            )

        generic_rewrite = self._rewrite_generic_reference(
            original_question=original_question,
            references=resolution.references,
        )

        if generic_rewrite:
            return RewrittenQuestion(
                original_question=original_question,
                rewritten_question=generic_rewrite,
                was_rewritten=generic_rewrite != original_question,
                rewrite_reason="resolved_implicit_reference",
                references_used=resolution.references,
                comparative_target=None,
                carry_previous_reasoning=False,
                warnings=warnings,
            )

        fallback_rewrite = self._rewrite_with_context_fallback(
            original_question=original_question,
            context=context,
            resolution=resolution,
        )

        return RewrittenQuestion(
            original_question=original_question,
            rewritten_question=fallback_rewrite,
            was_rewritten=fallback_rewrite != original_question,
            rewrite_reason=(
                "context_fallback"
                if fallback_rewrite != original_question
                else None
            ),
            references_used=resolution.references,
            comparative_target=None,
            carry_previous_reasoning=False,
            warnings=warnings,
        )

    def _rewrite_comparative_question(
        self,
        *,
        target: str,
        context: ConversationContext,
        resolution: ReferenceResolution,
    ) -> str:
        previous_reasoning = self._select_previous_reasoning(
            context=context,
            references=resolution.references,
        )

        if previous_reasoning:
            return (
                f"Applique à {target} le même raisonnement que celui "
                f"présenté précédemment : "
                f"« {previous_reasoning} »"
            )

        if context.previous_question:
            return (
                f"Analyse {target} en reprenant la méthode utilisée "
                f"pour répondre à la question précédente : "
                f"« {context.previous_question} »"
            )

        if context.last_independent_question:
            return (
                f"Analyse {target} en reprenant la méthode utilisée "
                f"pour la question : "
                f"« {context.last_independent_question} »"
            )

        if context.main_subject:
            return (
                f"Compare {target} avec le sujet précédemment étudié, "
                f"« {context.main_subject} », en conservant le même "
                f"cadre d'analyse."
            )

        return f"Analyse {target} selon le même cadre que précédemment."

    def _rewrite_category_reference(
        self,
        *,
        original_question: str,
        references: Sequence[ResolvedReference],
    ) -> str | None:
        category_references = tuple(
            reference
            for reference in references
            if reference.reference_type
            in {
                ReferenceType.HYPOTHESIS,
                ReferenceType.DEDUCTION,
                ReferenceType.EXPLICIT_CLAIM,
                ReferenceType.UNKNOWN,
                ReferenceType.MISSING_KNOWLEDGE,
                ReferenceType.WARNING,
                ReferenceType.SUMMARY,
            }
        )

        if not category_references:
            return None

        if len(category_references) == 1:
            reference = category_references[0]
            instruction = self._extract_instruction(original_question)
            label = self._label_for_reference(
                reference.reference_type
            )

            return (
                f"{instruction} {label} suivant : "
                f"« {reference.value} »"
            )

        grouped = self._format_reference_list(category_references)
        instruction = self._extract_instruction(original_question)
        plural_label = self._plural_label_for_references(
            category_references
        )

        return (
            f"{instruction} les {plural_label} suivants :\n"
            f"{grouped}"
        )

    def _rewrite_concept_reference(
        self,
        *,
        original_question: str,
        references: Sequence[ResolvedReference],
    ) -> str | None:
        concepts = tuple(
            reference
            for reference in references
            if reference.reference_type == ReferenceType.CONCEPT
        )

        non_concept_references = tuple(
            reference
            for reference in references
            if reference.reference_type
            not in {
                ReferenceType.CONCEPT,
                ReferenceType.COMPARATIVE_TARGET,
            }
        )

        if not concepts:
            return None

        if non_concept_references:
            return None

        all_concepts_are_explicit = all(
            self._contains_value(
                original_question,
                reference.value,
            )
            for reference in concepts
        )

        if all_concepts_are_explicit:
            return original_question

        if len(concepts) == 1:
            concept = concepts[0].value
            instruction = self._extract_instruction(
                original_question
            )

            return (
                f"{instruction} le concept suivant : "
                f"« {concept} »"
            )

        formatted = ", ".join(
            f"« {reference.value} »"
            for reference in concepts
        )

        return (
            f"Analyse les concepts suivants et leurs relations : "
            f"{formatted}."
        )

    def _rewrite_generic_reference(
        self,
        *,
        original_question: str,
        references: Sequence[ResolvedReference],
    ) -> str | None:
        candidates = tuple(
            reference
            for reference in references
            if reference.reference_type
            in {
                ReferenceType.PREVIOUS_ANSWER,
                ReferenceType.PREVIOUS_QUESTION,
                ReferenceType.MAIN_SUBJECT,
                ReferenceType.HYPOTHESIS,
                ReferenceType.DEDUCTION,
                ReferenceType.EXPLICIT_CLAIM,
            }
        )

        if not candidates:
            return None

        primary = max(
            candidates,
            key=lambda reference: reference.confidence,
        )

        instruction = self._extract_instruction(original_question)

        if primary.reference_type == ReferenceType.PREVIOUS_ANSWER:
            return (
                f"{instruction} le contenu de la réponse précédente : "
                f"« {primary.value} »"
            )

        if primary.reference_type == ReferenceType.PREVIOUS_QUESTION:
            return (
                f"{instruction} la question précédente : "
                f"« {primary.value} »"
            )

        if primary.reference_type == ReferenceType.MAIN_SUBJECT:
            return (
                f"{instruction} le sujet principal de la conversation : "
                f"« {primary.value} »"
            )

        label = self._label_for_reference(primary.reference_type)

        return (
            f"{instruction} {label} suivant : "
            f"« {primary.value} »"
        )

    def _rewrite_with_context_fallback(
        self,
        *,
        original_question: str,
        context: ConversationContext,
        resolution: ReferenceResolution,
    ) -> str:
        if resolution.unresolved_expressions:
            unresolved = ", ".join(
                f"« {expression} »"
                for expression in resolution.unresolved_expressions
            )

            return (
                f"{original_question} "
                f"Les références suivantes n'ont pas pu être résolues "
                f"dans le contexte disponible : {unresolved}."
            )

        if context.previous_question:
            return (
                f"{original_question} Cette demande se rapporte à la "
                f"question précédente : "
                f"« {context.previous_question} »"
            )

        if context.main_subject:
            return (
                f"{original_question} Le sujet principal du contexte est : "
                f"« {context.main_subject} »"
            )

        return original_question

    def _select_previous_reasoning(
        self,
        *,
        context: ConversationContext,
        references: Sequence[ResolvedReference],
    ) -> str | None:
        previous_answers = tuple(
            reference
            for reference in references
            if reference.reference_type == ReferenceType.PREVIOUS_ANSWER
        )

        if previous_answers:
            return previous_answers[-1].value

        if context.recent_summaries:
            return context.recent_summaries[-1]

        if context.deductions:
            return context.deductions[-1]

        if context.hypotheses:
            return context.hypotheses[-1]

        return None

    def _build_warnings(
        self,
        resolution: ReferenceResolution,
    ) -> tuple[str, ...]:
        warnings: list[str] = []

        for expression in resolution.unresolved_expressions:
            warnings.append(
                f"Référence non résolue : {expression}"
            )

        if (
            resolution.requires_context
            and not resolution.references
            and not resolution.comparative_target
        ):
            warnings.append(
                "La question dépend du contexte, mais aucune référence "
                "précise n'a été résolue."
            )

        return self._unique_strings(warnings)

    @staticmethod
    def _extract_instruction(question: str) -> str:
        cleaned = QuestionRewriter._clean_text(question)
        normalized = cleaned.casefold()

        mappings = (
            ("pourquoi", "Explique pourquoi"),
            ("comment", "Explique comment"),
            ("développe", "Développe"),
            ("developpe", "Développe"),
            ("explique", "Explique"),
            ("précise", "Précise"),
            ("precise", "Précise"),
            ("approfondis", "Approfondis"),
            ("justifie", "Justifie"),
            ("démontre", "Démontre"),
            ("demontre", "Démontre"),
            (
                "prouve",
                "Établis les éléments qui soutiennent",
            ),
            ("compare", "Compare"),
            ("analyse", "Analyse"),
            ("énumère", "Énumère"),
            ("enumere", "Énumère"),
            ("liste", "Liste"),
        )

        for prefix, instruction in mappings:
            if normalized.startswith(prefix):
                return instruction

        return "Analyse"

    @staticmethod
    def _label_for_reference(
        reference_type: ReferenceType,
    ) -> str:
        labels = {
            ReferenceType.HYPOTHESIS: "l'hypothèse",
            ReferenceType.DEDUCTION: "la déduction",
            ReferenceType.EXPLICIT_CLAIM: "l'affirmation",
            ReferenceType.UNKNOWN: "l'inconnue",
            ReferenceType.MISSING_KNOWLEDGE: (
                "la connaissance manquante"
            ),
            ReferenceType.WARNING: "l'avertissement",
            ReferenceType.SUMMARY: "le résumé",
            ReferenceType.PREVIOUS_ANSWER: (
                "la réponse précédente"
            ),
            ReferenceType.PREVIOUS_QUESTION: (
                "la question précédente"
            ),
            ReferenceType.MAIN_SUBJECT: "le sujet principal",
            ReferenceType.CONCEPT: "le concept",
        }

        return labels.get(reference_type, "l'élément")

    def _plural_label_for_references(
        self,
        references: Sequence[ResolvedReference],
    ) -> str:
        types = {
            reference.reference_type
            for reference in references
        }

        if len(types) != 1:
            return "éléments"

        reference_type = next(iter(types))

        labels = {
            ReferenceType.HYPOTHESIS: "hypothèses",
            ReferenceType.DEDUCTION: "déductions",
            ReferenceType.EXPLICIT_CLAIM: "affirmations",
            ReferenceType.UNKNOWN: "inconnues",
            ReferenceType.MISSING_KNOWLEDGE: (
                "connaissances manquantes"
            ),
            ReferenceType.WARNING: "avertissements",
            ReferenceType.SUMMARY: "résumés",
        }

        return labels.get(reference_type, "éléments")

    @staticmethod
    def _format_reference_list(
        references: Sequence[ResolvedReference],
    ) -> str:
        return "\n".join(
            f"{index}. « {reference.value} »"
            for index, reference in enumerate(
                references,
                start=1,
            )
        )

    @staticmethod
    def _contains_value(
        question: str,
        value: str,
    ) -> bool:
        return value.casefold() in question.casefold()

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(
            str(value or "").strip().split()
        )

    @staticmethod
    def _unique_strings(
        values: Iterable[str],
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = QuestionRewriter._clean_text(value)

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return tuple(result)