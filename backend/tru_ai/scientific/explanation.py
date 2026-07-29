from __future__ import annotations

from collections import Counter
from dataclasses import is_dataclass
from enum import Enum
from typing import Any

from tru_ai.cognitive.reasoning.models import (
    OperatorTrace,
    ReasoningResult,
    ReasoningStage,
    ReasoningStep,
    ScientificTheoryRevision,
    TheoryEvolution,
)
from tru_ai.scientific.models import (
    JsonObject,
    ScientificHumanReadable,
    ScientificStageCard,
    ScientificSummary,
)


class ScientificExplanationService:
    """Build reusable public explanations from actual reasoning results."""

    def summary(self, result: ReasoningResult) -> ScientificSummary:
        """Return neutral counts derived from the supplied result."""

        revision_count = len(result.scientific_theory_revisions)
        return ScientificSummary(
            theory_maturity=result.theory.to_dict().get("maturity", {}),
            claim_count=self._claim_count(result),
            prediction_count=len(result.scientific_predictions),
            scenario_count=len(result.scientific_scenarios),
            simulation_count=len(result.scenario_simulations),
            observation_count=len(result.scientific_observations),
            verification_report_count=len(result.verification_reports),
            verification_status_counts=dict(
                Counter(
                    report.status.value
                    for report in result.verification_reports
                )
            ),
            falsification_report_count=len(result.falsification_reports),
            falsified_count=sum(
                1 for report in result.falsification_reports
                if report.falsified
            ),
            has_theory_evolution=self._has_theory_evolution(
                result.theory_evolution
            ),
            has_revision_recommendations=revision_count > 0,
            revision_recommendation_count=revision_count,
            scientific_gap_count=len(result.scientific_gaps),
        )

    def human_readable(
        self,
        result: ReasoningResult,
    ) -> ScientificHumanReadable:
        """Return readable text without discarding repeated result items."""

        limitations = [
            limitation
            for report in result.verification_reports
            for limitation in report.limitations
        ]
        return ScientificHumanReadable(
            overview=result.synthesis,
            observations=[
                self._observation_text(item)
                for item in result.scientific_observations
            ],
            predictions=[
                self._prediction_text(item)
                for item in result.scientific_predictions
            ],
            verification_reports=[
                self._verification_text(item)
                for item in result.verification_reports
            ],
            falsification_reports=[
                self._falsification_text(item)
                for item in result.falsification_reports
            ],
            revision_recommendations=[
                self._revision_text(item)
                for item in result.scientific_theory_revisions
            ],
            scientific_gaps=[
                self._gap_text(item)
                for item in result.scientific_gaps
            ],
            limitations=limitations,
        )

    def stage_cards(
        self,
        result: ReasoningResult,
    ) -> list[ScientificStageCard]:
        """Return cards for stages represented by actual operator traces."""

        steps_by_position = {
            (step.position, step.stage): step
            for step in result.plan.steps
        }
        return [
            self._stage_card(
                result=result,
                trace=trace,
                step=steps_by_position.get((trace.position, trace.stage)),
            )
            for trace in result.operator_trace
        ]

    def explain(
        self,
        result: ReasoningResult,
    ) -> tuple[ScientificSummary, ScientificHumanReadable, list[ScientificStageCard]]:
        """Build all reusable explanation projections."""

        return (
            self.summary(result),
            self.human_readable(result),
            self.stage_cards(result),
        )

    @staticmethod
    def _claim_count(result: ReasoningResult) -> int:
        if result.theory_graph.claims:
            return len(result.theory_graph.claims)
        return len(result.claims)

    @staticmethod
    def _has_theory_evolution(evolution: TheoryEvolution) -> bool:
        return any(
            (
                evolution.added_claims,
                evolution.removed_claims,
                evolution.strengthened_claims,
                evolution.weakened_claims,
            )
        )

    @staticmethod
    def _prediction_text(item: Any) -> str:
        parts = [
            f"{item.prediction_id}: {item.text}",
            f"status={item.status}",
            f"confidence={item.confidence}",
            f"confidence_level={item.confidence_level.value}",
        ]
        if item.expected_observation:
            parts.append(f"expected_observation={item.expected_observation}")
        if item.falsification_condition:
            parts.append(
                f"falsification_condition={item.falsification_condition}"
            )
        return "; ".join(parts)

    @staticmethod
    def _observation_text(item: Any) -> str:
        parts = [f"{item.observation_id}: {item.text}"]
        if item.prediction_id:
            parts.append(f"prediction_id={item.prediction_id}")
        if item.compatibility_score is not None:
            parts.append(f"compatibility_score={item.compatibility_score}")
        parts.append(
            "matches_falsification_condition="
            f"{item.matches_falsification_condition}"
        )
        return "; ".join(parts)

    @staticmethod
    def _verification_text(item: Any) -> str:
        parts = [
            f"{item.report_id}: prediction_id={item.prediction_id}",
            f"status={item.status.value}",
            f"consistency_score={item.consistency_score}",
            f"evidence_score={item.evidence_score}",
        ]
        if item.rationale:
            parts.append(f"rationale={item.rationale}")
        return "; ".join(parts)

    @staticmethod
    def _falsification_text(item: Any) -> str:
        parts = [
            f"{item.report_id}: prediction_id={item.prediction_id}",
            f"falsified={item.falsified}",
            f"formal_test_possible={item.formal_test_possible}",
            "falsification_condition_met="
            f"{item.falsification_condition_met}",
            f"revision_required={item.revision_required}",
        ]
        if item.rationale:
            parts.append(f"rationale={item.rationale}")
        return "; ".join(parts)

    @staticmethod
    def _revision_text(item: ScientificTheoryRevision) -> str:
        parts = [
            f"{item.revision_id}: prediction_id={item.prediction_id}",
            f"recommended_action={item.action}",
            "applied=False",
        ]
        if item.reason:
            parts.append(f"reason={item.reason}")
        return "; ".join(parts)

    @staticmethod
    def _gap_text(item: Any) -> str:
        parts = [
            f"{item.gap_id}: {item.description}",
            f"gap_type={item.gap_type}",
        ]
        if item.required_action:
            parts.append(f"required_action={item.required_action}")
        return "; ".join(parts)

    def _stage_card(
        self,
        *,
        result: ReasoningResult,
        trace: OperatorTrace,
        step: ReasoningStep | None,
    ) -> ScientificStageCard:
        stage = trace.stage.value
        details: JsonObject = {
            "operator": trace.operator,
            "position": trace.position,
            "inputs": list(trace.inputs),
            "outputs": list(trace.outputs),
            "required": step.required if step is not None else None,
            "objective": step.objective if step is not None else None,
            "error": trace.error,
        }
        return ScientificStageCard(
            stage=stage,
            title=self._stage_title(trace.stage),
            status=trace.status.value,
            summary=self._stage_summary(trace=trace, step=step),
            details=details,
            data=self._stage_data(result=result, stage=trace.stage),
        )

    @staticmethod
    def _stage_title(stage: ReasoningStage) -> str:
        return stage.value.replace("_", " ").title()

    @staticmethod
    def _stage_summary(
        *,
        trace: OperatorTrace,
        step: ReasoningStep | None,
    ) -> str:
        if trace.error:
            return trace.error
        if step is not None:
            return step.objective
        return f"{trace.operator} returned {trace.status.value}."

    def _stage_data(
        self,
        *,
        result: ReasoningResult,
        stage: ReasoningStage,
    ) -> JsonObject:
        if stage is ReasoningStage.OBSERVATION:
            return {
                "scientific_observations": self._items(
                    result.scientific_observations
                ),
            }
        if stage is ReasoningStage.THEORY_EVOLUTION:
            return {
                "theory_evolution": self._item(result.theory_evolution),
                "theory_history": self._item(result.theory_history),
            }
        if stage is ReasoningStage.PREDICTION:
            return {
                "scientific_predictions": self._items(
                    result.scientific_predictions
                ),
                "scientific_scenarios": self._items(
                    result.scientific_scenarios
                ),
                "scenario_simulations": self._items(
                    result.scenario_simulations
                ),
            }
        if stage is ReasoningStage.VERIFICATION:
            return {
                "scientific_observations": self._items(
                    result.scientific_observations
                ),
                "verification_reports": self._items(
                    result.verification_reports
                ),
            }
        if stage is ReasoningStage.FALSIFICATION:
            return {
                "falsification_reports": self._items(
                    result.falsification_reports
                ),
                "scientific_theory_revisions": self._items(
                    result.scientific_theory_revisions
                ),
            }
        if stage is ReasoningStage.SCIENTIFIC_GAPS:
            return {
                "scientific_gaps": self._items(result.scientific_gaps),
            }
        if stage is ReasoningStage.THEORY_CONSTRUCTION:
            return {
                "theory_graph": self._item(result.theory_graph),
                "theory": self._item(result.theory),
            }
        if stage is ReasoningStage.SYNTHESIS:
            return {"synthesis": result.synthesis}
        return {}

    @staticmethod
    def _items(values: tuple[Any, ...]) -> list[Any]:
        return [ScientificExplanationService._item(value) for value in values]

    @staticmethod
    def _item(value: Any) -> Any:
        if hasattr(value, "to_dict"):
            return value.to_dict()
        if isinstance(value, Enum):
            return value.value
        if is_dataclass(value):
            return {
                key: ScientificExplanationService._item(item)
                for key, item in value.__dict__.items()
            }
        if isinstance(value, tuple):
            return [ScientificExplanationService._item(item) for item in value]
        if isinstance(value, list):
            return [ScientificExplanationService._item(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): ScientificExplanationService._item(item)
                for key, item in value.items()
            }
        return value
