from __future__ import annotations

import hashlib
import json
from typing import Protocol

from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningPlan,
    ReasoningResult,
)
from tru_ai.scientific.adapters import ScientificInputAdapter
from tru_ai.scientific.explanation import ScientificExplanationService
from tru_ai.scientific.models import (
    JsonObject,
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
    ScientificTheoryRevisionRecommendation,
)


class ScientificPlanner(Protocol):
    """Planner interface required by the scientific service."""

    def plan(self, request: ReasoningRequest) -> ReasoningPlan:
        ...


class ScientificExecutor(Protocol):
    """Executor interface required by the scientific service."""

    def execute(
        self,
        plan: ReasoningPlan,
        *,
        conversation_context: dict[str, object] | None = None,
    ) -> ReasoningResult:
        ...


class ScientificService:
    """Application facade for generic scientific reasoning."""

    def __init__(
        self,
        *,
        planner: ScientificPlanner | None = None,
        executor: ScientificExecutor | None = None,
        adapter: ScientificInputAdapter | None = None,
        explanation_service: ScientificExplanationService | None = None,
    ) -> None:
        self._planner = planner or ReasoningPlanner()
        self._executor = executor or ReasoningExecutor()
        self._adapter = adapter or ScientificInputAdapter()
        self._explanation_service = (
            explanation_service or ScientificExplanationService()
        )

    def analyze(
        self,
        request: ScientificAnalysisRequest,
    ) -> ScientificAnalysisResult:
        """Run the existing reasoning pipeline and project its result."""

        reasoning_request = ReasoningRequest(
            question=request.question,
            intent=request.intent,
        )
        conversation_context = self._adapter.to_conversation_context(request)
        plan = self._planner.plan(reasoning_request)
        result = self._executor.execute(
            plan,
            conversation_context=conversation_context,
        )
        return self._project_result(request=request, result=result)

    def _project_result(
        self,
        *,
        request: ScientificAnalysisRequest,
        result: ReasoningResult,
    ) -> ScientificAnalysisResult:
        raw_result = result.to_dict()
        summary = self._explanation_service.summary(result)
        human_readable = None
        stage_cards = []
        if request.options.include_human_readable:
            human_readable = self._explanation_service.human_readable(result)
            stage_cards = self._explanation_service.stage_cards(result)
        return ScientificAnalysisResult(
            analysis_id=self._analysis_id(request=request, raw_result=raw_result),
            execution_plan=result.plan,
            summary=summary,
            human_readable=human_readable,
            stage_cards=stage_cards,
            operator_trace=list(result.operator_trace),
            theory_graph=result.theory_graph,
            theory_evolution=result.theory_evolution,
            theory_history=result.theory_history,
            scientific_predictions=list(result.scientific_predictions),
            scientific_scenarios=list(result.scientific_scenarios),
            scenario_simulations=list(result.scenario_simulations),
            scientific_observations=list(result.scientific_observations),
            verification_reports=list(result.verification_reports),
            falsification_reports=list(result.falsification_reports),
            scientific_theory_revisions=[
                ScientificTheoryRevisionRecommendation(revision=revision)
                for revision in result.scientific_theory_revisions
            ],
            scientific_gaps=list(result.scientific_gaps),
            raw_result=raw_result if request.options.include_raw_result else None,
        )

    @staticmethod
    def _analysis_id(
        *,
        request: ScientificAnalysisRequest,
        raw_result: JsonObject,
    ) -> str:
        payload = {
            "request": request.model_dump(mode="json"),
            "result": raw_result,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]
