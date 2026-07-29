from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tru_ai.cognitive.reasoning.models import (
    FalsificationReport,
    OperatorTrace,
    ReasoningPlan,
    ScenarioSimulation,
    ScientificGap,
    ScientificObservation,
    ScientificPrediction,
    ScientificScenario,
    ScientificTheoryRevision,
    TheoryClaim,
    TheoryEvolution,
    TheoryGraph,
    TheoryHistory,
    VerificationReport,
)


JsonObject = dict[str, Any]


class ScientificModel(BaseModel):
    """Base configuration for public scientific API contracts."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )


class ScientificAnalysisOptions(ScientificModel):
    """Execution options for a future scientific analysis request."""

    include_raw_result: bool = False
    include_human_readable: bool = True
    persist: bool = False


class ScientificTheoryInput(ScientificModel):
    """Public representation of a user-provided scientific theory."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    claims: list[TheoryClaim] = Field(default_factory=list)
    relations: list[tuple[str, str, str]] = Field(default_factory=list)

    def to_theory_graph(self) -> TheoryGraph:
        """Return the stable internal graph representation."""

        return TheoryGraph(
            theory_id=self.id,
            name=self.name,
            claims=tuple(self.claims),
            relations=tuple(self.relations),
        )


class ScientificBaselineInput(ScientificModel):
    """Baseline supplied as a full theory or as standalone claims."""

    theory: ScientificTheoryInput | None = None
    claims: list[TheoryClaim] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_baseline_content(self) -> ScientificBaselineInput:
        if self.theory is None and not self.claims:
            message = "baseline_theory requires a theory or at least one claim"
            raise ValueError(message)
        return self


class ScientificPredictionRuleInput(ScientificModel):
    """Public input used to describe an explicit prediction rule."""

    id: str = Field(min_length=1)
    statement: str | None = None
    condition: str = Field(min_length=1)
    consequence: str = Field(min_length=1)
    source_claim_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_observation: str | None = None
    falsification_condition: str | None = None
    horizon: str | None = None


class ScientificAnalysisRequest(ScientificModel):
    """Public request contract for the future POST /scientific/analyze API."""

    question: str = Field(min_length=1)
    intent: str = Field(default="scientific_research", min_length=1)
    theory_version: str | None = None
    theory: ScientificTheoryInput | None = None
    baseline_theory: ScientificBaselineInput | None = None
    theory_history: TheoryHistory | None = None
    comparison_theories: list[ScientificTheoryInput] = Field(
        default_factory=list
    )
    predictions: list[ScientificPrediction] = Field(default_factory=list)
    prediction_rules: list[ScientificPredictionRuleInput] = Field(
        default_factory=list
    )
    scenarios: list[ScientificScenario] = Field(default_factory=list)
    scientific_observations: list[ScientificObservation] = Field(
        default_factory=list
    )
    options: ScientificAnalysisOptions = Field(
        default_factory=ScientificAnalysisOptions
    )


class ScientificSummary(ScientificModel):
    """Neutral counts and statuses derived from actual scientific results."""

    theory_maturity: JsonObject = Field(default_factory=dict)
    claim_count: int = Field(default=0, ge=0)
    prediction_count: int = Field(default=0, ge=0)
    scenario_count: int = Field(default=0, ge=0)
    simulation_count: int = Field(default=0, ge=0)
    observation_count: int = Field(default=0, ge=0)
    verification_report_count: int = Field(default=0, ge=0)
    verification_status_counts: dict[str, int] = Field(default_factory=dict)
    falsification_report_count: int = Field(default=0, ge=0)
    falsified_count: int = Field(default=0, ge=0)
    has_theory_evolution: bool = False
    has_revision_recommendations: bool = False
    revision_recommendation_count: int = Field(default=0, ge=0)
    scientific_gap_count: int = Field(default=0, ge=0)


class ScientificStageCard(ScientificModel):
    """Generic public representation of one scientific reasoning stage."""

    stage: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(default="not_run", min_length=1)
    summary: str | None = None
    details: JsonObject = Field(default_factory=dict)
    data: JsonObject = Field(default_factory=dict)


class ScientificHumanReadable(ScientificModel):
    """Human-readable projection built from real scientific results."""

    overview: str | None = None
    observations: list[str] = Field(default_factory=list)
    predictions: list[str] = Field(default_factory=list)
    verification_reports: list[str] = Field(default_factory=list)
    falsification_reports: list[str] = Field(default_factory=list)
    revision_recommendations: list[str] = Field(default_factory=list)
    scientific_gaps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ScientificTheoryRevisionRecommendation(ScientificModel):
    """A recommended theory revision, not an applied mutation."""

    revision: ScientificTheoryRevision
    applied: Literal[False] = False


class ScientificAnalysisResult(ScientificModel):
    """Stable public projection of a scientific reasoning execution."""

    analysis_id: str = Field(min_length=1)
    execution_plan: ReasoningPlan | JsonObject
    summary: ScientificSummary = Field(default_factory=ScientificSummary)
    human_readable: ScientificHumanReadable | None = None
    stage_cards: list[ScientificStageCard] = Field(default_factory=list)
    operator_trace: list[OperatorTrace] = Field(default_factory=list)
    theory_graph: TheoryGraph | None = None
    theory_evolution: TheoryEvolution | None = None
    theory_history: TheoryHistory | None = None
    scientific_predictions: list[ScientificPrediction] = Field(
        default_factory=list
    )
    scientific_scenarios: list[ScientificScenario] = Field(
        default_factory=list
    )
    scenario_simulations: list[ScenarioSimulation] = Field(
        default_factory=list
    )
    scientific_observations: list[ScientificObservation] = Field(
        default_factory=list
    )
    verification_reports: list[VerificationReport] = Field(
        default_factory=list
    )
    falsification_reports: list[FalsificationReport] = Field(
        default_factory=list
    )
    scientific_theory_revisions: list[
        ScientificTheoryRevisionRecommendation
    ] = Field(default_factory=list)
    scientific_gaps: list[ScientificGap] = Field(default_factory=list)
    raw_result: JsonObject | None = None
