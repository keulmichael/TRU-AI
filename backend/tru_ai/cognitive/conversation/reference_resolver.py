from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable, Sequence

from tru_ai.cognitive.conversation.context_builder import (
    ConversationContext,
)


class ReferenceType(str, Enum):
    """
    Catégories de références conversationnelles reconnues.

    Le résolveur ne modifie pas encore la question. Il identifie uniquement
    les éléments du contexte auxquels la question semble faire référence.
    """

    NONE = "none"
    PREVIOUS_QUESTION = "previous_question"
    PREVIOUS_ANSWER = "previous_answer"
    MAIN_SUBJECT = "main_subject"
    CONCEPT = "concept"
    EXPLICIT_CLAIM = "explicit_claim"
    DEDUCTION = "deduction"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"
    MISSING_KNOWLEDGE = "missing_knowledge"
    WARNING = "warning"
    SUMMARY = "summary"
    COMPARATIVE_TARGET = "comparative_target"


@dataclass(frozen=True)
class ResolvedReference:
    """
    Référence unique résolue à partir de la question et du contexte.
    """

    reference_type: ReferenceType
    value: str
    source_index: int | None
    matched_expression: str
    confidence: float

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["reference_type"] = self.reference_type.value
        return payload


@dataclass(frozen=True)
class ReferenceResolution:
    """
    Résultat complet de la résolution des références d'une question.
    """

    original_question: str
    normalized_question: str
    references: tuple[ResolvedReference, ...]
    unresolved_expressions: tuple[str, ...]
    requires_context: bool
    comparative_target: str | None
    carry_previous_reasoning: bool

    @property
    def has_references(self) -> bool:
        return bool(self.references)

    @property
    def primary_reference(self) -> ResolvedReference | None:
        if not self.references:
            return None

        return max(
            self.references,
            key=lambda reference: reference.confidence,
        )

    def references_of_type(
        self,
        reference_type: ReferenceType,
    ) -> tuple[ResolvedReference, ...]:
        return tuple(
            reference
            for reference in self.references
            if reference.reference_type == reference_type
        )

    def to_dict(self) -> dict:
        return {
            "original_question": self.original_question,
            "normalized_question": self.normalized_question,
            "references": [
                reference.to_dict()
                for reference in self.references
            ],
            "unresolved_expressions": list(
                self.unresolved_expressions
            ),
            "requires_context": self.requires_context,
            "comparative_target": self.comparative_target,
            "carry_previous_reasoning": self.carry_previous_reasoning,
            "has_references": self.has_references,
            "primary_reference": (
                self.primary_reference.to_dict()
                if self.primary_reference
                else None
            ),
        }


class ReferenceResolver:
    """
    Résout les références implicites contenues dans une question.

    Exemples :

    - « Pourquoi ? »
      -> dernière question ou dernière réponse ;

    - « Développe la deuxième hypothèse. »
      -> deuxième hypothèse du contexte ;

    - « Explique cette déduction. »
      -> dernière déduction disponible ;

    - « Et pour la dépression ? »
      -> nouvelle cible comparative avec conservation du raisonnement ;

    - « Parle davantage du Delta. »
      -> concept Delta déjà reconnu dans la conversation.

    Le composant reste déterministe. Il ne crée aucune connaissance et ne
    réalise aucun raisonnement scientifique.
    """

    _ORDINAL_WORDS = {
        "premier": 1,
        "premiere": 1,
        "1er": 1,
        "1ere": 1,
        "un": 1,
        "une": 1,
        "deuxieme": 2,
        "second": 2,
        "seconde": 2,
        "2e": 2,
        "2eme": 2,
        "deux": 2,
        "troisieme": 3,
        "3e": 3,
        "3eme": 3,
        "trois": 3,
        "quatrieme": 4,
        "4e": 4,
        "4eme": 4,
        "quatre": 4,
        "cinquieme": 5,
        "5e": 5,
        "5eme": 5,
        "cinq": 5,
        "sixieme": 6,
        "6e": 6,
        "6eme": 6,
        "six": 6,
        "septieme": 7,
        "7e": 7,
        "7eme": 7,
        "sept": 7,
        "huitieme": 8,
        "8e": 8,
        "8eme": 8,
        "huit": 8,
        "neuvieme": 9,
        "9e": 9,
        "9eme": 9,
        "neuf": 9,
        "dixieme": 10,
        "10e": 10,
        "10eme": 10,
        "dix": 10,
    }

    _CATEGORY_PATTERNS = {
        ReferenceType.HYPOTHESIS: (
            "hypothese",
            "hypotheses",
        ),
        ReferenceType.DEDUCTION: (
            "deduction",
            "deductions",
            "conclusion",
            "conclusions",
        ),
        ReferenceType.EXPLICIT_CLAIM: (
            "affirmation",
            "affirmations",
            "element explicite",
            "elements explicites",
            "fait",
            "faits",
        ),
        ReferenceType.UNKNOWN: (
            "inconnu",
            "inconnue",
            "inconnus",
            "inconnues",
            "incertitude",
            "incertitudes",
        ),
        ReferenceType.MISSING_KNOWLEDGE: (
            "connaissance manquante",
            "connaissances manquantes",
            "information manquante",
            "informations manquantes",
        ),
        ReferenceType.WARNING: (
            "avertissement",
            "avertissements",
            "mise en garde",
            "mises en garde",
            "limite",
            "limites",
        ),
        ReferenceType.SUMMARY: (
            "resume",
            "resumes",
            "synthese",
            "syntheses",
        ),
    }

    _GENERIC_REFERENCE_EXPRESSIONS = (
        "cela",
        "ca",
        "ceci",
        "ce point",
        "cet element",
        "cette idee",
        "cette analyse",
        "cette explication",
        "cette reponse",
        "la reponse precedente",
        "le raisonnement precedent",
        "ce raisonnement",
        "le meme raisonnement",
        "la meme analyse",
        "celui-ci",
        "celle-ci",
        "celui la",
        "celle la",
    )

    _SHORT_CONTEXTUAL_QUESTIONS = (
        "pourquoi",
        "comment",
        "developpe",
        "explique",
        "precise",
        "continue",
        "approfondis",
        "justifie",
        "prouve",
        "demontre",
    )

    _COMPARATIVE_PATTERNS = (
        re.compile(
            r"^(?:et\s+)?pour\s+(.+?)(?:\s*[?!.])?$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(?:et\s+)?(?:qu['’]en est-il|qu['’]en est il)"
            r"\s+(?:de|du|des|pour)\s+(.+?)(?:\s*[?!.])?$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(?:et\s+)?dans\s+le\s+cas\s+(?:de|du|des)\s+"
            r"(.+?)(?:\s*[?!.])?$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(?:et\s+)?applique\s+(?:cela|ca|ce raisonnement|"
            r"la meme analyse)\s+(?:a|à|au|aux)\s+"
            r"(.+?)(?:\s*[?!.])?$",
            re.IGNORECASE,
        ),
    )

    def resolve(
        self,
        question: str,
        context: ConversationContext,
    ) -> ReferenceResolution:
        original_question = self._clean_text(question)
        normalized_question = self._normalize(original_question)

        if not original_question:
            return ReferenceResolution(
                original_question="",
                normalized_question="",
                references=(),
                unresolved_expressions=(),
                requires_context=False,
                comparative_target=None,
                carry_previous_reasoning=False,
            )

        references: list[ResolvedReference] = []
        unresolved_expressions: list[str] = []

        comparative_target = self._extract_comparative_target(
            original_question
        )

        if comparative_target:
            references.append(
                ResolvedReference(
                    reference_type=ReferenceType.COMPARATIVE_TARGET,
                    value=comparative_target,
                    source_index=None,
                    matched_expression=comparative_target,
                    confidence=0.98,
                )
            )

        category_references, category_unresolved = (
            self._resolve_category_references(
                normalized_question=normalized_question,
                context=context,
            )
        )

        references.extend(category_references)
        unresolved_expressions.extend(category_unresolved)

        concept_references = self._resolve_concept_references(
            original_question=original_question,
            normalized_question=normalized_question,
            concepts=context.concepts,
        )
        references.extend(concept_references)

        generic_references = self._resolve_generic_references(
            normalized_question=normalized_question,
            context=context,
            existing_references=references,
        )
        references.extend(generic_references)

        short_reference = None

        if not unresolved_expressions:
            short_reference = self._resolve_short_contextual_question(
                normalized_question=normalized_question,
                context=context,
                existing_references=references,
            )

        if short_reference is not None:
            references.append(short_reference)

        references = list(self._unique_references(references))

        requires_context = self._requires_context(
            normalized_question=normalized_question,
            references=references,
            unresolved_expressions=unresolved_expressions,
            comparative_target=comparative_target,
        )

        carry_previous_reasoning = comparative_target is not None

        return ReferenceResolution(
            original_question=original_question,
            normalized_question=normalized_question,
            references=tuple(references),
            unresolved_expressions=self._unique_strings(
                unresolved_expressions
            ),
            requires_context=requires_context,
            comparative_target=comparative_target,
            carry_previous_reasoning=carry_previous_reasoning,
        )

    def _resolve_category_references(
        self,
        *,
        normalized_question: str,
        context: ConversationContext,
    ) -> tuple[
        tuple[ResolvedReference, ...],
        tuple[str, ...],
    ]:
        references: list[ResolvedReference] = []
        unresolved: list[str] = []

        for reference_type, category_terms in (
            self._CATEGORY_PATTERNS.items()
        ):
            matched_term = self._find_expression(
                normalized_question,
                category_terms,
            )

            if not matched_term:
                continue

            values = self._values_for_type(
                context=context,
                reference_type=reference_type,
            )

            ordinal = self._extract_ordinal_near_category(
                normalized_question=normalized_question,
                category_terms=category_terms,
            )

            if ordinal is not None:
                reference = self._reference_at_index(
                    values=values,
                    reference_type=reference_type,
                    one_based_index=ordinal,
                    matched_expression=(
                        f"{self._ordinal_label(ordinal)} "
                        f"{matched_term}"
                    ),
                )

                if reference:
                    references.append(reference)
                else:
                    unresolved.append(
                        f"{self._ordinal_label(ordinal)} "
                        f"{matched_term}"
                    )

                continue

            if self._contains_plural_request(
                normalized_question=normalized_question,
                category_terms=category_terms,
            ):
                for index, value in enumerate(values, start=1):
                    references.append(
                        ResolvedReference(
                            reference_type=reference_type,
                            value=value,
                            source_index=index,
                            matched_expression=matched_term,
                            confidence=0.92,
                        )
                    )

                if not values:
                    unresolved.append(matched_term)

                continue

            if values:
                references.append(
                    ResolvedReference(
                        reference_type=reference_type,
                        value=values[-1],
                        source_index=len(values),
                        matched_expression=matched_term,
                        confidence=0.88,
                    )
                )
            else:
                unresolved.append(matched_term)

        return (
            tuple(references),
            self._unique_strings(unresolved),
        )

    def _resolve_concept_references(
        self,
        *,
        original_question: str,
        normalized_question: str,
        concepts: Sequence[str],
    ) -> tuple[ResolvedReference, ...]:
        references: list[ResolvedReference] = []

        for index, concept in enumerate(concepts, start=1):
            normalized_concept = self._normalize(concept)

            if not normalized_concept:
                continue

            if not self._contains_expression(
                normalized_question,
                normalized_concept,
            ):
                continue

            matched_expression = self._matched_original_expression(
                original_text=original_question,
                target=concept,
            )

            references.append(
                ResolvedReference(
                    reference_type=ReferenceType.CONCEPT,
                    value=concept,
                    source_index=index,
                    matched_expression=matched_expression or concept,
                    confidence=0.97,
                )
            )

        return tuple(references)

    def _resolve_generic_references(
        self,
        *,
        normalized_question: str,
        context: ConversationContext,
        existing_references: Sequence[ResolvedReference],
    ) -> tuple[ResolvedReference, ...]:
        references: list[ResolvedReference] = []

        matched_expression = self._find_expression(
            normalized_question,
            self._GENERIC_REFERENCE_EXPRESSIONS,
        )

        if not matched_expression:
            return ()

        if existing_references:
            return ()

        if (
            "reponse" in matched_expression
            or "analyse" in matched_expression
            or "explication" in matched_expression
            or "raisonnement" in matched_expression
        ):
            if context.recent_summaries:
                references.append(
                    ResolvedReference(
                        reference_type=ReferenceType.PREVIOUS_ANSWER,
                        value=context.recent_summaries[-1],
                        source_index=len(context.recent_summaries),
                        matched_expression=matched_expression,
                        confidence=0.93,
                    )
                )
                return tuple(references)

        reference = self._best_previous_content_reference(
            context=context,
            matched_expression=matched_expression,
        )

        if reference:
            references.append(reference)

        return tuple(references)

    def _resolve_short_contextual_question(
        self,
        *,
        normalized_question: str,
        context: ConversationContext,
        existing_references: Sequence[ResolvedReference],
    ) -> ResolvedReference | None:
        if existing_references:
            return None

        stripped_question = normalized_question.strip(" ?!.")

        is_short_question = (
            len(stripped_question.split()) <= 4
            and any(
                stripped_question == expression
                or stripped_question.startswith(
                    f"{expression} "
                )
                for expression in self._SHORT_CONTEXTUAL_QUESTIONS
            )
        )

        if not is_short_question:
            return None

        if context.recent_summaries:
            return ResolvedReference(
                reference_type=ReferenceType.PREVIOUS_ANSWER,
                value=context.recent_summaries[-1],
                source_index=len(context.recent_summaries),
                matched_expression=stripped_question,
                confidence=0.86,
            )

        if context.previous_question:
            return ResolvedReference(
                reference_type=ReferenceType.PREVIOUS_QUESTION,
                value=context.previous_question,
                source_index=None,
                matched_expression=stripped_question,
                confidence=0.82,
            )

        if context.last_independent_question:
            return ResolvedReference(
                reference_type=ReferenceType.PREVIOUS_QUESTION,
                value=context.last_independent_question,
                source_index=None,
                matched_expression=stripped_question,
                confidence=0.80,
            )

        return None

    def _best_previous_content_reference(
        self,
        *,
        context: ConversationContext,
        matched_expression: str,
    ) -> ResolvedReference | None:
        candidates: tuple[
            tuple[ReferenceType, Sequence[str], float],
            ...,
        ] = (
            (
                ReferenceType.HYPOTHESIS,
                context.hypotheses,
                0.84,
            ),
            (
                ReferenceType.DEDUCTION,
                context.deductions,
                0.83,
            ),
            (
                ReferenceType.EXPLICIT_CLAIM,
                context.explicit_claims,
                0.82,
            ),
            (
                ReferenceType.PREVIOUS_ANSWER,
                context.recent_summaries,
                0.81,
            ),
        )

        for reference_type, values, confidence in candidates:
            if not values:
                continue

            return ResolvedReference(
                reference_type=reference_type,
                value=values[-1],
                source_index=len(values),
                matched_expression=matched_expression,
                confidence=confidence,
            )

        if context.previous_question:
            return ResolvedReference(
                reference_type=ReferenceType.PREVIOUS_QUESTION,
                value=context.previous_question,
                source_index=None,
                matched_expression=matched_expression,
                confidence=0.78,
            )

        if context.main_subject:
            return ResolvedReference(
                reference_type=ReferenceType.MAIN_SUBJECT,
                value=context.main_subject,
                source_index=None,
                matched_expression=matched_expression,
                confidence=0.75,
            )

        return None

    def _extract_comparative_target(
        self,
        question: str,
    ) -> str | None:
        for pattern in self._COMPARATIVE_PATTERNS:
            match = pattern.match(question.strip())

            if not match:
                continue

            target = self._clean_target(match.group(1))

            if target:
                return target

        return None

    def _extract_ordinal_near_category(
        self,
        *,
        normalized_question: str,
        category_terms: Sequence[str],
    ) -> int | None:
        ordinal_pattern = "|".join(
            sorted(
                (
                    re.escape(word)
                    for word in self._ORDINAL_WORDS
                ),
                key=len,
                reverse=True,
            )
        )

        category_pattern = "|".join(
            sorted(
                (
                    re.escape(term)
                    for term in category_terms
                ),
                key=len,
                reverse=True,
            )
        )

        before_pattern = re.compile(
            rf"\b({ordinal_pattern})\b"
            rf"(?:\s+\w+){{0,2}}\s+"
            rf"\b(?:{category_pattern})\b"
        )

        after_pattern = re.compile(
            rf"\b(?:{category_pattern})\b"
            rf"(?:\s+\w+){{0,2}}\s+"
            rf"\b({ordinal_pattern})\b"
        )

        for pattern in (before_pattern, after_pattern):
            match = pattern.search(normalized_question)

            if not match:
                continue

            ordinal_word = match.group(1)
            return self._ORDINAL_WORDS.get(ordinal_word)

        numeric_match = re.search(
            rf"\b(?:{category_pattern})\b"
            r"(?:\s+(?:numero|n))?\s*(\d+)\b",
            normalized_question,
        )

        if numeric_match:
            return int(numeric_match.group(1))

        return None

    def _reference_at_index(
        self,
        *,
        values: Sequence[str],
        reference_type: ReferenceType,
        one_based_index: int,
        matched_expression: str,
    ) -> ResolvedReference | None:
        zero_based_index = one_based_index - 1

        if zero_based_index < 0:
            return None

        if zero_based_index >= len(values):
            return None

        return ResolvedReference(
            reference_type=reference_type,
            value=values[zero_based_index],
            source_index=one_based_index,
            matched_expression=matched_expression,
            confidence=0.99,
        )

    @staticmethod
    def _values_for_type(
        *,
        context: ConversationContext,
        reference_type: ReferenceType,
    ) -> Sequence[str]:
        mapping = {
            ReferenceType.HYPOTHESIS: context.hypotheses,
            ReferenceType.DEDUCTION: context.deductions,
            ReferenceType.EXPLICIT_CLAIM: (
                context.explicit_claims
            ),
            ReferenceType.UNKNOWN: context.unknowns,
            ReferenceType.MISSING_KNOWLEDGE: (
                context.missing_knowledge
            ),
            ReferenceType.WARNING: context.warnings,
            ReferenceType.SUMMARY: context.recent_summaries,
        }

        return mapping.get(reference_type, ())

    def _requires_context(
        self,
        *,
        normalized_question: str,
        references: Sequence[ResolvedReference],
        unresolved_expressions: Sequence[str],
        comparative_target: str | None,
    ) -> bool:
        if references:
            return True

        if unresolved_expressions:
            return True

        if comparative_target:
            return True

        if self._find_expression(
            normalized_question,
            self._GENERIC_REFERENCE_EXPRESSIONS,
        ):
            return True

        stripped = normalized_question.strip(" ?!.")

        return (
            len(stripped.split()) <= 4
            and any(
                stripped == expression
                or stripped.startswith(f"{expression} ")
                for expression in self._SHORT_CONTEXTUAL_QUESTIONS
            )
        )

    @staticmethod
    def _contains_plural_request(
        *,
        normalized_question: str,
        category_terms: Sequence[str],
    ) -> bool:
        plural_indicators = (
            "toutes",
            "tous",
            "les",
            "plusieurs",
            "liste",
            "enumerer",
            "enumere",
        )

        contains_plural_term = any(
            term.endswith("s")
            and ReferenceResolver._contains_expression(
                normalized_question,
                term,
            )
            for term in category_terms
        )

        if not contains_plural_term:
            return False

        return any(
            ReferenceResolver._contains_expression(
                normalized_question,
                indicator,
            )
            for indicator in plural_indicators
        ) or normalized_question.startswith(
            "quelles "
        ) or normalized_question.startswith(
            "quels "
        )

    @staticmethod
    def _contains_expression(
        text: str,
        expression: str,
    ) -> bool:
        if not expression:
            return False

        pattern = re.compile(
            rf"(?<!\w){re.escape(expression)}(?!\w)"
        )

        return bool(pattern.search(text))

    def _find_expression(
        self,
        text: str,
        expressions: Iterable[str],
    ) -> str | None:
        sorted_expressions = sorted(
            expressions,
            key=len,
            reverse=True,
        )

        for expression in sorted_expressions:
            normalized_expression = self._normalize(expression)

            if self._contains_expression(
                text,
                normalized_expression,
            ):
                return normalized_expression

        return None

    @staticmethod
    def _matched_original_expression(
        *,
        original_text: str,
        target: str,
    ) -> str | None:
        match = re.search(
            re.escape(target),
            original_text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return match.group(0)

    @staticmethod
    def _clean_target(value: str) -> str:
        target = ReferenceResolver._clean_text(value)

        target = re.sub(
            r"^(?:le|la|les|l['’]|un|une|des)\s+",
            "",
            target,
            flags=re.IGNORECASE,
        )

        target = target.strip(" ?!.:;,")

        return target

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(str(value or "").strip().split())

    @staticmethod
    def _normalize(value: str) -> str:
        cleaned = ReferenceResolver._clean_text(value)

        decomposed = unicodedata.normalize(
            "NFD",
            cleaned,
        )

        without_accents = "".join(
            character
            for character in decomposed
            if unicodedata.category(character) != "Mn"
        )

        normalized = without_accents.casefold()
        normalized = normalized.replace("’", "'")

        return " ".join(normalized.split())

    @staticmethod
    def _ordinal_label(index: int) -> str:
        labels = {
            1: "première",
            2: "deuxième",
            3: "troisième",
            4: "quatrième",
            5: "cinquième",
            6: "sixième",
            7: "septième",
            8: "huitième",
            9: "neuvième",
            10: "dixième",
        }

        return labels.get(index, f"numéro {index}")

    @staticmethod
    def _unique_strings(
        values: Iterable[str],
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = ReferenceResolver._clean_text(value)

            if not cleaned:
                continue

            identity = ReferenceResolver._normalize(cleaned)

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return tuple(result)

    @staticmethod
    def _unique_references(
        references: Iterable[ResolvedReference],
    ) -> tuple[ResolvedReference, ...]:
        result: list[ResolvedReference] = []
        seen: set[tuple[str, str, int | None]] = set()

        for reference in references:
            identity = (
                reference.reference_type.value,
                ReferenceResolver._normalize(reference.value),
                reference.source_index,
            )

            if identity in seen:
                continue

            seen.add(identity)
            result.append(reference)

        return tuple(result)