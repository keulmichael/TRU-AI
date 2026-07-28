from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines import (
    ContextEngine,
    ContradictionEngine,
    DeductionEngine,
    DeltaEngine,
    ExplicitFactsEngine,
    HypothesisEngine,
    MissingKnowledgeEngine,
    ObservationEngine,
    RecognitionEngine,
    RecognitionMeaningEngine,
    ReflexivityEngine,
    ReasoningEngine,
    ReasoningExecutionState,
    SynthesisEngine,
    TheoryConstructionEngine, TheoryComparisonEngine, TheoryEvolutionEngine,
    PredictionEngine, ScientificGapEngine,
)
from tru_ai.cognitive.reasoning.models import ReasoningPlan, ReasoningResult


class ReasoningExecutor:
    """Exécute séquentiellement un ReasoningPlan."""

    def __init__(
        self,
        *,
        handlers: tuple[ReasoningEngine, ...] | None = None,
        engines: tuple[ReasoningEngine, ...] | None = None,
    ) -> None:
        if handlers is not None and engines is not None:
            raise ValueError(
                "Utilisez soit « handlers », soit « engines », pas les deux."
            )

        selected_engines = engines or handlers or self._default_engines()
        self._engines = {
            engine.stage: engine
            for engine in selected_engines
        }

        if len(self._engines) != len(selected_engines):
            raise ValueError(
                "Un seul handler peut être enregistré par étape."
            )

    def execute(
        self,
        plan: ReasoningPlan,
        *,
        conversation_context: Mapping[str, Any] | None = None,
    ) -> ReasoningResult:
        state = ReasoningExecutionState(
            question=plan.question,
            intent=plan.intent,
            conversation_context=dict(conversation_context or {}),
        )

        for step in plan.steps:
            engine = self._engines.get(step.stage)

            if engine is None:
                if step.required:
                    raise ValueError(
                        "Aucun handler n'est disponible pour l'étape "
                        f"obligatoire « {step.stage.value} »."
                    )
                continue

            output = engine.execute(step=step, state=state)
            if output is not None:
                state.step_outputs[step.stage.value] = dict(output)

        return ReasoningResult(
            plan=plan,
            claims=tuple(state.claims),
            recognition_graph=state.recognition_graph,
            recognition_patterns=tuple(state.recognition_patterns),
            delta_comparisons=tuple(state.delta_comparisons),
            reflexive_graph=state.reflexive_graph,
            reflexive_relations=tuple(state.reflexive_relations),
            reflexive_loops=tuple(state.reflexive_loops),
            recognition_meaning_graph=state.recognition_meaning_graph,
            recognition_meanings=tuple(state.recognition_meanings),
            recognition_gaps=tuple(state.recognition_gaps),
            theory_graph=state.theory_graph,
            theory=state.theory,
            theory_comparisons=tuple(state.theory_comparisons),
            theory_evolution=state.theory_evolution,
            scientific_predictions=tuple(state.scientific_predictions),
            scientific_gaps=tuple(state.scientific_gaps),
            contradictions=tuple(state.contradictions),
            missing_knowledge=tuple(state.missing_knowledge),
            synthesis=state.synthesis,
        )

    @staticmethod
    def _default_engines() -> tuple[ReasoningEngine, ...]:
        return (
            ObservationEngine(),
            ContextEngine(),
            ExplicitFactsEngine(),
            DeductionEngine(),
            HypothesisEngine(),
            RecognitionEngine(),
            DeltaEngine(),
            ReflexivityEngine(),
            RecognitionMeaningEngine(),
            TheoryConstructionEngine(),
            TheoryComparisonEngine(),
            TheoryEvolutionEngine(),
            PredictionEngine(),
            ScientificGapEngine(),
            ContradictionEngine(),
            MissingKnowledgeEngine(),
            SynthesisEngine(),
        )
