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
    PredictionEngine, VerificationEngine, FalsificationEngine, ScientificGapEngine,
)
from tru_ai.cognitive.reasoning.models import (
    OperatorStatus, OperatorTrace, ReasoningPlan, ReasoningResult, ReasoningStage,
)


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

        operator_trace: list[OperatorTrace] = []

        for step in plan.steps:
            engine = self._engines.get(step.stage)

            if engine is None:
                operator_trace.append(OperatorTrace(
                    operator=self._operator_name(step.stage),
                    stage=step.stage,
                    position=step.position,
                    status=OperatorStatus.SKIPPED,
                    inputs=step.inputs,
                    outputs=(),
                    error="No handler available.",
                ))
                if step.required:
                    raise ValueError(
                        "Aucun handler n'est disponible pour l'étape "
                        f"obligatoire « {step.stage.value} »."
                    )
                continue

            try:
                output = engine.execute(step=step, state=state)
            except Exception as exc:
                operator_trace.append(OperatorTrace(
                    operator=self._operator_name(step.stage), stage=step.stage,
                    position=step.position, status=OperatorStatus.FAILED,
                    inputs=step.inputs, outputs=(), error=str(exc),
                ))
                raise
            actual_outputs = tuple(output.keys()) if output is not None else ()
            operator_trace.append(OperatorTrace(
                operator=self._operator_name(step.stage), stage=step.stage,
                position=step.position, status=OperatorStatus.SUCCESS,
                inputs=step.inputs, outputs=actual_outputs,
            ))
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
            theory_history=state.theory_history,
            operator_trace=tuple(operator_trace),
            scientific_predictions=tuple(state.scientific_predictions),
            scientific_scenarios=tuple(state.scientific_scenarios),
            scenario_simulations=tuple(state.scenario_simulations),
            scientific_observations=tuple(state.scientific_observations),
            verification_reports=tuple(state.verification_reports),
            falsification_reports=tuple(state.falsification_reports),
            scientific_theory_revisions=tuple(state.scientific_theory_revisions),
            scientific_gaps=tuple(state.scientific_gaps),
            contradictions=tuple(state.contradictions),
            missing_knowledge=tuple(state.missing_knowledge),
            synthesis=state.synthesis,
        )

    @staticmethod
    def _operator_name(stage: ReasoningStage) -> str:
        aliases = {
            ReasoningStage.OBSERVATION: "ObservationOperator",
            ReasoningStage.DELTA: "DeltaOperator",
            ReasoningStage.RECOGNITION: "RecognitionOperator",
            ReasoningStage.REFLEXIVITY: "ReflexivityOperator",
            ReasoningStage.RECOGNITION_MEANING: "IntegrationOperator",
            ReasoningStage.THEORY_CONSTRUCTION: "TheoryConstructionOperator",
            ReasoningStage.THEORY_EVOLUTION: "TheoryEvolutionOperator",
            ReasoningStage.SYNTHESIS: "ManifestationOperator",
        }
        return aliases.get(stage, f"{''.join(part.title() for part in stage.value.split('_'))}Operator")

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
            VerificationEngine(),
            FalsificationEngine(),
            ScientificGapEngine(),
            ContradictionEngine(),
            MissingKnowledgeEngine(),
            SynthesisEngine(),
        )
