from __future__ import annotations

from dataclasses import dataclass

import pytest

from tru_ai.cognitive.reasoning.executor import (
    ReasoningExecutionState,
    ReasoningExecutor,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningPlan,
    ReasoningRequest,
    ReasoningStage,
    ReasoningStep,
    TruthStatus,
)
from tru_ai.cognitive.reasoning.planner import ReasoningPlanner


def build_plan(
    *,
    intent: str = "concept_explanation",
) -> ReasoningPlan:
    return ReasoningPlanner().plan(
        ReasoningRequest(
            question="Explique le Delta.",
            intent=intent,
        )
    )


def test_executor_executes_complete_plan() -> None:
    executor = ReasoningExecutor()
    plan = build_plan()

    result = executor.execute(
        plan,
        conversation_context={
            "explicit_claims": [
                "Le Delta représente un écart.",
            ],
            "deductions": [
                "Un écart suppose deux états comparables.",
            ],
            "hypotheses": [
                "Le Delta pourrait participer à la prédiction.",
            ],
            "contradictions": [
                "La définition exacte du second état reste discutée.",
            ],
            "missing_knowledge": [
                "Une validation expérimentale manque.",
            ],
        },
    )

    assert len(result.claims) == 3
    assert result.claims[0].status == TruthStatus.EXPLICIT
    assert result.claims[1].status == TruthStatus.DEDUCTION
    assert result.claims[2].status == TruthStatus.HYPOTHESIS

    assert result.contradictions == (
        "La définition exacte du second état reste discutée.",
    )
    assert result.missing_knowledge == (
        "Une validation expérimentale manque.",
    )
    assert result.synthesis == (
        "Le raisonnement a identifié 1 élément(s) explicite(s), "
        "1 déduction(s), 1 hypothèse(s), "
        "1 contradiction(s) et 1 connaissance(s) manquante(s)."
    )


def test_executor_does_not_invent_claims() -> None:
    executor = ReasoningExecutor()

    result = executor.execute(
        build_plan(),
        conversation_context={},
    )

    assert result.claims == ()
    assert result.contradictions == ()
    assert result.missing_knowledge == ()
    assert result.synthesis is not None


def test_executor_normalizes_and_deduplicates_context_values() -> None:
    executor = ReasoningExecutor()

    result = executor.execute(
        build_plan(),
        conversation_context={
            "explicit_claims": [
                "  Le Delta est un écart. ",
                "Le Delta est un écart.",
                123,
            ],
            "contradictions": "  Contradiction unique. ",
        },
    )

    explicit_claims = [
        claim
        for claim in result.claims
        if claim.status == TruthStatus.EXPLICIT
    ]

    assert [claim.text for claim in explicit_claims] == [
        "Le Delta est un écart.",
    ]
    assert result.contradictions == (
        "Contradiction unique.",
    )


def test_reduced_plan_only_executes_selected_stages() -> None:
    executor = ReasoningExecutor()

    result = executor.execute(
        build_plan(intent="supporting_arguments"),
        conversation_context={
            "explicit_claims": ["Fait."],
            "deductions": ["Déduction."],
            "hypotheses": ["Hypothèse non demandée."],
        },
    )

    assert [
        claim.status
        for claim in result.claims
    ] == [
        TruthStatus.EXPLICIT,
        TruthStatus.DEDUCTION,
    ]


@dataclass
class CustomHandler:
    stage: ReasoningStage = ReasoningStage.OBSERVATION

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ):
        state.normalized_problem = "Observation personnalisée"
        return {
            "normalized_problem": state.normalized_problem,
        }


def test_executor_accepts_custom_handlers() -> None:
    plan = ReasoningPlan(
        question="Question",
        intent="custom",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.OBSERVATION,
                objective="Observer",
            ),
        ),
    )

    executor = ReasoningExecutor(
        handlers=(CustomHandler(),),
    )

    result = executor.execute(plan)

    assert result.plan == plan
    assert result.claims == ()
    assert result.synthesis is None


def test_missing_required_handler_is_rejected() -> None:
    plan = ReasoningPlan(
        question="Question",
        intent="custom",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.SYNTHESIS,
                objective="Synthétiser",
                required=True,
            ),
        ),
    )

    executor = ReasoningExecutor(
        handlers=(CustomHandler(),),
    )

    with pytest.raises(
        ValueError,
        match="Aucun handler n'est disponible",
    ):
        executor.execute(plan)


def test_missing_optional_handler_is_ignored() -> None:
    plan = ReasoningPlan(
        question="Question",
        intent="custom",
        steps=(
            ReasoningStep(
                position=1,
                stage=ReasoningStage.SYNTHESIS,
                objective="Synthétiser",
                required=False,
            ),
        ),
    )

    executor = ReasoningExecutor(
        handlers=(CustomHandler(),),
    )

    result = executor.execute(plan)

    assert result.synthesis is None


def test_duplicate_handlers_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Un seul handler",
    ):
        ReasoningExecutor(
            handlers=(
                CustomHandler(),
                CustomHandler(),
            ),
        )


def test_result_is_json_serializable() -> None:
    executor = ReasoningExecutor()

    payload = executor.execute(
        build_plan(),
        conversation_context={
            "explicit_claims": ["Fait."],
        },
    ).to_dict()

    assert payload["plan"]["question"] == "Explique le Delta."
    assert payload["claims"][0]["status"] == "EXPLICITE"
    assert isinstance(payload["contradictions"], list)
    assert isinstance(payload["missing_knowledge"], list)


def test_executor_detects_explicit_reflexive_contradiction() -> None:
    executor = ReasoningExecutor()

    result = executor.execute(
        build_plan(),
        conversation_context={
            "recognition_graph": {
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                ],
                "relations": [
                    {
                        "id": "r1",
                        "source": "a",
                        "target": "b",
                        "type": "reconnait",
                        "attributes": {
                            "contradicts_relation_id": "r2"
                        },
                    },
                    {
                        "id": "r2",
                        "source": "a",
                        "target": "b",
                        "type": "nie",
                    },
                ],
            }
        },
    )

    assert len(result.contradictions) == 1
    assert result.contradictions[0].startswith(
        "Contradiction réflexive explicite :"
    )
    assert "1 contradiction(s) réflexive(s) explicite(s)" in (
        result.synthesis or ""
    )


def test_executor_preserves_historical_synthesis_without_reflexive_conflict() -> None:
    executor = ReasoningExecutor()

    result = executor.execute(
        build_plan(),
        conversation_context={
            "explicit_claims": ["Fait."],
            "contradictions": ["Contradiction déclarée."],
        },
    )

    assert result.synthesis == (
        "Le raisonnement a identifié 1 élément(s) explicite(s), "
        "0 déduction(s), 0 hypothèse(s), "
        "1 contradiction(s) et 0 connaissance(s) manquante(s)."
    )
