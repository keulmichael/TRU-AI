from __future__ import annotations

from dataclasses import dataclass

import pytest

from tru_ai.cognitive.reasoning import (
    ContextEngine,
    ContradictionEngine,
    DeductionEngine,
    ExplicitFactsEngine,
    HypothesisEngine,
    ObservationEngine,
    RecognitionGraph,
    RecognitionNode,
    RecognitionRelation,
    ReflexiveLoop,
    ReflexiveRelation,
    ReasoningExecutor,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningStage,
    ReasoningStep,
    SynthesisEngine,
    TruthStatus,
)
from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_string_sequence,
    normalize_text,
)
from tru_ai.cognitive.reasoning.planner import ReasoningPlanner


def build_state() -> ReasoningExecutionState:
    return ReasoningExecutionState(
        question="  Explique   le Delta. ",
        intent="concept_explanation",
        conversation_context={
            "explicit_claims": [
                "  Le Delta est un écart. ",
                "Le Delta est un écart.",
            ],
            "facts": [
                "Deux états sont comparés.",
            ],
            "deductions": [
                "Une comparaison suppose une relation.",
            ],
            "hypotheses": [
                "Le Delta pourrait guider l'adaptation.",
            ],
        },
    )


def build_step(
    stage: ReasoningStage,
) -> ReasoningStep:
    return ReasoningStep(
        position=1,
        stage=stage,
        objective="Tester.",
    )


def test_normalize_text_is_deterministic() -> None:
    assert normalize_text("  A   B  ") == "A B"
    assert normalize_text(123) == ""


def test_normalize_string_sequence_deduplicates_values() -> None:
    assert normalize_string_sequence(
        [" A ", "A", "B", 123]
    ) == ["A", "B"]


def test_observation_engine_normalizes_question() -> None:
    state = build_state()

    output = ObservationEngine().execute(
        step=build_step(ReasoningStage.OBSERVATION),
        state=state,
    )

    assert state.normalized_problem == "Explique le Delta."
    assert output == {
        "normalized_problem": "Explique le Delta.",
    }


def test_context_engine_copies_conversation_context() -> None:
    state = build_state()

    ContextEngine().execute(
        step=build_step(ReasoningStage.CONTEXT),
        state=state,
    )

    assert state.relevant_context == state.conversation_context
    assert state.relevant_context is not state.conversation_context


def test_explicit_facts_engine_combines_supported_keys() -> None:
    state = build_state()
    state.relevant_context = dict(state.conversation_context)

    output = ExplicitFactsEngine().execute(
        step=build_step(ReasoningStage.EXPLICIT_CLAIMS),
        state=state,
    )

    assert [
        claim.text
        for claim in state.claims
    ] == [
        "Le Delta est un écart.",
        "Deux états sont comparés.",
    ]
    assert all(
        claim.status == TruthStatus.EXPLICIT
        for claim in state.claims
    )
    assert len(output["explicit_claims"]) == 2


def test_deduction_engine_classifies_deductions() -> None:
    state = build_state()
    state.relevant_context = dict(state.conversation_context)

    DeductionEngine().execute(
        step=build_step(ReasoningStage.DEDUCTIONS),
        state=state,
    )

    assert state.claims[0].status == TruthStatus.DEDUCTION


def test_hypothesis_engine_classifies_hypotheses() -> None:
    state = build_state()
    state.relevant_context = dict(state.conversation_context)

    HypothesisEngine().execute(
        step=build_step(ReasoningStage.HYPOTHESES),
        state=state,
    )

    assert state.claims[0].status == TruthStatus.HYPOTHESIS


def test_synthesis_engine_counts_each_category() -> None:
    state = build_state()
    state.relevant_context = dict(state.conversation_context)

    ExplicitFactsEngine().execute(
        step=build_step(ReasoningStage.EXPLICIT_CLAIMS),
        state=state,
    )
    DeductionEngine().execute(
        step=build_step(ReasoningStage.DEDUCTIONS),
        state=state,
    )
    HypothesisEngine().execute(
        step=build_step(ReasoningStage.HYPOTHESES),
        state=state,
    )

    output = SynthesisEngine().execute(
        step=build_step(ReasoningStage.SYNTHESIS),
        state=state,
    )

    assert output["synthesis"] == (
        "Le raisonnement a identifié 2 élément(s) explicite(s), "
        "1 déduction(s), 1 hypothèse(s), "
        "0 contradiction(s) et 0 connaissance(s) manquante(s)."
    )


def test_default_executor_uses_modular_engines() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(
            question="Explique le Delta.",
            intent="concept_explanation",
        )
    )

    result = ReasoningExecutor().execute(
        plan,
        conversation_context=build_state().conversation_context,
    )

    assert len(result.claims) == 4
    assert result.synthesis is not None


@dataclass
class CustomObservationEngine:
    stage: ReasoningStage = ReasoningStage.OBSERVATION

    def execute(self, *, step, state):
        state.normalized_problem = "Personnalisé"
        return {
            "normalized_problem": "Personnalisé",
        }


def test_executor_accepts_engines_keyword() -> None:
    plan = ReasoningPlan(
        question="Question",
        intent="custom",
        steps=(
            build_step(ReasoningStage.OBSERVATION),
        ),
    )

    result = ReasoningExecutor(
        engines=(CustomObservationEngine(),),
    ).execute(plan)

    assert result.plan == plan


def test_executor_preserves_handlers_keyword_compatibility() -> None:
    plan = ReasoningPlan(
        question="Question",
        intent="custom",
        steps=(
            build_step(ReasoningStage.OBSERVATION),
        ),
    )

    result = ReasoningExecutor(
        handlers=(CustomObservationEngine(),),
    ).execute(plan)

    assert result.plan == plan


def test_executor_rejects_handlers_and_engines_together() -> None:
    custom = (CustomObservationEngine(),)

    with pytest.raises(
        ValueError,
        match="pas les deux",
    ):
        ReasoningExecutor(
            handlers=custom,
            engines=custom,
        )


def test_contradiction_engine_preserves_declared_contradictions() -> None:
    state = build_state()
    state.relevant_context = {
        "contradictions": [
            " Contradiction déclarée. ",
            "Contradiction déclarée.",
        ]
    }

    output = ContradictionEngine().execute(
        step=build_step(ReasoningStage.CONTRADICTIONS),
        state=state,
    )

    assert state.contradictions == ["Contradiction déclarée."]
    assert output["explicit_reflexive_contradictions"] == []
    assert output["potential_reflexive_tensions"] == []


def test_contradiction_engine_detects_explicit_relation_reference() -> None:
    state = build_state()
    state.relevant_context = {}
    state.recognition_graph = RecognitionGraph(
        nodes=(
            RecognitionNode(node_id="a", label="A"),
            RecognitionNode(node_id="b", label="B"),
        ),
        relations=(
            RecognitionRelation(
                relation_id="r1",
                source_id="a",
                target_id="b",
                relation_type="reconnait",
                attributes={"contradicts_relation_id": "r2"},
            ),
            RecognitionRelation(
                relation_id="r2",
                source_id="a",
                target_id="b",
                relation_type="nie",
            ),
        ),
    )

    output = ContradictionEngine().execute(
        step=build_step(ReasoningStage.CONTRADICTIONS),
        state=state,
    )

    assert len(output["explicit_reflexive_contradictions"]) == 1
    assert output["explicit_reflexive_contradictions"][0].startswith(
        "Contradiction réflexive explicite :"
    )


def test_contradiction_engine_detects_opposite_explicit_polarities() -> None:
    state = build_state()
    state.relevant_context = {}
    state.recognition_graph = RecognitionGraph(
        relations=(
            RecognitionRelation(
                relation_id="r1",
                source_id="a",
                target_id="b",
                relation_type="relation",
                attributes={"polarity": "positive"},
            ),
            RecognitionRelation(
                relation_id="r2",
                source_id="a",
                target_id="b",
                relation_type="relation",
                attributes={"polarity": "negative"},
            ),
        )
    )

    output = ContradictionEngine().execute(
        step=build_step(ReasoningStage.CONTRADICTIONS),
        state=state,
    )

    assert len(output["explicit_reflexive_contradictions"]) == 1
    assert "polarités opposées" in output[
        "explicit_reflexive_contradictions"
    ][0]


def test_contradiction_engine_distinguishes_potential_tension() -> None:
    state = build_state()
    state.relevant_context = {}
    state.recognition_graph = RecognitionGraph(
        relations=(
            RecognitionRelation(
                relation_id="r1",
                source_id="a",
                target_id="b",
                relation_type="observe",
                attributes={"tension": True},
            ),
        )
    )

    output = ContradictionEngine().execute(
        step=build_step(ReasoningStage.CONTRADICTIONS),
        state=state,
    )

    assert output["explicit_reflexive_contradictions"] == []
    assert len(output["potential_reflexive_tensions"]) == 1
    assert output["potential_reflexive_tensions"][0].startswith(
        "Tension réflexive potentielle :"
    )


def test_contradiction_engine_detects_mixed_polarity_closed_loop() -> None:
    state = build_state()
    state.relevant_context = {}
    state.recognition_graph = RecognitionGraph(
        relations=(
            RecognitionRelation(
                relation_id="r1",
                source_id="a",
                target_id="b",
                relation_type="agit",
                attributes={"polarity": "positive"},
            ),
            RecognitionRelation(
                relation_id="r2",
                source_id="b",
                target_id="a",
                relation_type="agit",
                attributes={"polarity": "negative"},
            ),
        )
    )
    state.reflexive_loops.append(
        ReflexiveLoop(
            relations=(
                ReflexiveRelation(
                    observer="a",
                    observed="b",
                    relation="agit",
                    recognition_level=2,
                ),
                ReflexiveRelation(
                    observer="b",
                    observed="a",
                    relation="agit",
                    recognition_level=2,
                ),
            ),
            closed=True,
        )
    )

    output = ContradictionEngine().execute(
        step=build_step(ReasoningStage.CONTRADICTIONS),
        state=state,
    )

    assert len(output["potential_reflexive_tensions"]) == 1
    assert "boucle fermée" in output["potential_reflexive_tensions"][0]
