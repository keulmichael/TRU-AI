from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from tru_ai.cognitive.reasoning.models import (
    DeltaComparison,
    RecognitionGraph,
    RecognitionPattern,
    RecognitionGap,
    RecognitionMeaning,
    RecognitionMeaningGraph,
    ReflexiveGraph,
    ReflexiveLoop,
    ReflexiveRelation,
    ReasoningClaim,
    ReasoningStage,
    ReasoningStep,
    TruthStatus,
    Theory, TheoryGraph, TheoryComparison, TheoryEvolution, ScientificPrediction, ScientificGap,
)


@dataclass
class ReasoningExecutionState:
    """
    État mutable partagé entre les moteurs de raisonnement.

    Il centralise les résultats intermédiaires sans porter lui-même
    de logique cognitive.
    """

    question: str
    intent: str
    conversation_context: dict[str, Any] = field(default_factory=dict)
    normalized_problem: str | None = None
    relevant_context: dict[str, Any] = field(default_factory=dict)
    claims: list[ReasoningClaim] = field(default_factory=list)
    recognition_graph: RecognitionGraph = field(
        default_factory=RecognitionGraph
    )
    recognition_patterns: list[RecognitionPattern] = field(
        default_factory=list
    )
    delta_comparisons: list[DeltaComparison] = field(default_factory=list)
    reflexive_graph: ReflexiveGraph = field(
        default_factory=ReflexiveGraph
    )
    reflexive_relations: list[ReflexiveRelation] = field(
        default_factory=list
    )
    reflexive_loops: list[ReflexiveLoop] = field(
        default_factory=list
    )
    recognition_meaning_graph: RecognitionMeaningGraph = field(
        default_factory=RecognitionMeaningGraph
    )
    recognition_meanings: list[RecognitionMeaning] = field(
        default_factory=list
    )
    recognition_gaps: list[RecognitionGap] = field(default_factory=list)
    theory_graph: TheoryGraph = field(default_factory=TheoryGraph)
    theory: Theory = field(default_factory=Theory)
    theory_comparisons: list[TheoryComparison] = field(default_factory=list)
    theory_evolution: TheoryEvolution = field(default_factory=TheoryEvolution)
    scientific_predictions: list[ScientificPrediction] = field(default_factory=list)
    scientific_gaps: list[ScientificGap] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    missing_knowledge: list[str] = field(default_factory=list)
    synthesis: str | None = None
    step_outputs: dict[str, Any] = field(default_factory=dict)

    def claims_by_status(
        self,
        status: TruthStatus,
    ) -> tuple[ReasoningClaim, ...]:
        return tuple(
            claim
            for claim in self.claims
            if claim.status == status
        )


class ReasoningEngine(Protocol):
    """
    Contrat commun à tous les moteurs spécialisés.
    """

    stage: ReasoningStage

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any] | None:
        ...


def normalize_text(value: Any) -> str:
    """
    Normalise une valeur textuelle sans interprétation.
    """

    if not isinstance(value, str):
        return ""

    return " ".join(value.strip().split())


def normalize_string_sequence(value: Any) -> list[str]:
    """
    Normalise et déduplique une chaîne ou une séquence de chaînes.
    """

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, (list, tuple)):
        return []

    result: list[str] = []

    for item in value:
        normalized = normalize_text(item)

        if normalized and normalized not in result:
            result.append(normalized)

    return result
