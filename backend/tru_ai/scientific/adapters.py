from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.scientific.models import (
    ScientificAnalysisRequest,
    ScientificBaselineInput,
    ScientificPredictionRuleInput,
    ScientificTheoryInput,
)


class ScientificInputAdapter:
    """Build the reasoning conversation context from public inputs."""

    KEY_THEORY_VERSION = "theory_version"
    KEY_THEORY = "theory"
    KEY_BASELINE_THEORY = "baseline_theory"
    KEY_THEORY_HISTORY = "theory_history"
    KEY_COMPARISON_THEORIES = "comparison_theories"
    KEY_PREDICTIONS = "predictions"
    KEY_PREDICTION_RULES = "prediction_rules"
    KEY_SCENARIOS = "scenarios"
    KEY_SCIENTIFIC_OBSERVATIONS = "scientific_observations"

    def to_conversation_context(
        self,
        request: ScientificAnalysisRequest,
    ) -> dict[str, Any]:
        """Map only user-provided scientific data into reasoning context."""

        context: dict[str, Any] = {}

        if request.theory_version is not None:
            context[self.KEY_THEORY_VERSION] = request.theory_version
        if request.theory is not None:
            context[self.KEY_THEORY] = self._theory_payload(request.theory)
        if request.baseline_theory is not None:
            context[self.KEY_BASELINE_THEORY] = self._baseline_payload(
                request.baseline_theory
            )
        if request.theory_history is not None:
            context[self.KEY_THEORY_HISTORY] = request.theory_history.to_dict()
        if request.comparison_theories:
            context[self.KEY_COMPARISON_THEORIES] = [
                self._theory_payload(theory)
                for theory in request.comparison_theories
            ]
        if request.predictions:
            context[self.KEY_PREDICTIONS] = [
                prediction.to_dict() for prediction in request.predictions
            ]
        if request.prediction_rules:
            context[self.KEY_PREDICTION_RULES] = [
                self._prediction_rule_payload(rule)
                for rule in request.prediction_rules
            ]
        if request.scenarios:
            context[self.KEY_SCENARIOS] = [
                scenario.to_dict() for scenario in request.scenarios
            ]
        if request.scientific_observations:
            context[self.KEY_SCIENTIFIC_OBSERVATIONS] = [
                observation.to_dict()
                for observation in request.scientific_observations
            ]

        return context

    @staticmethod
    def _theory_payload(theory: ScientificTheoryInput) -> dict[str, Any]:
        return {
            "id": theory.id,
            "name": theory.name,
            "claims": [claim.to_dict() for claim in theory.claims],
            "relations": [
                {"source": source, "target": target, "type": relation}
                for source, target, relation in theory.relations
            ],
        }

    def _baseline_payload(
        self,
        baseline: ScientificBaselineInput,
    ) -> dict[str, Any]:
        if baseline.theory is not None:
            return self._theory_payload(baseline.theory)
        return {
            "claims": [claim.to_dict() for claim in baseline.claims],
        }

    @staticmethod
    def _prediction_rule_payload(
        rule: ScientificPredictionRuleInput,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": rule.id,
            "if": rule.condition,
            "then": rule.consequence,
            "source_claim_ids": list(rule.source_claim_ids),
        }
        optional: Mapping[str, Any] = {
            "statement": rule.statement,
            "confidence": rule.confidence,
            "expected_observation": rule.expected_observation,
            "falsification_condition": rule.falsification_condition,
            "horizon": rule.horizon,
        }
        for key, value in optional.items():
            if value is not None:
                payload[key] = value
        return payload
