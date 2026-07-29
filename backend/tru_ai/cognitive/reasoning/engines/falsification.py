from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tru_ai.cognitive.models import deterministic_id
from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState, normalize_text
from tru_ai.cognitive.reasoning.models import (
    FalsificationReport, ReasoningStage, ReasoningStep, ScientificObservation,
    ScientificTheoryRevision, VerificationReport, VerificationStatus,
)


def _items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _clamp(value: Any, default: float) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 6)
    except (TypeError, ValueError):
        return default


class VerificationEngine:
    stage = ReasoningStage.VERIFICATION

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        observations = self._build_observations(state)
        reports = [self._verify(prediction, observations) for prediction in state.scientific_predictions]
        state.scientific_observations = observations
        state.verification_reports = reports
        return {
            "scientific_observations": [item.to_dict() for item in observations],
            "verification_reports": [item.to_dict() for item in reports],
        }

    @staticmethod
    def _build_observations(state: ReasoningExecutionState) -> list[ScientificObservation]:
        raw = state.conversation_context.get("scientific_observations")
        if raw is None:
            raw = state.conversation_context.get("observations", [])
        result = []
        for index, item in enumerate(_items(raw), start=1):
            text = normalize_text(item.get("text") or item.get("observation"))
            if not text:
                continue
            prediction_id = normalize_text(item.get("prediction_id")) or None
            evidence = item.get("evidence_ids", item.get("evidence", []))
            if isinstance(evidence, str):
                evidence = [evidence]
            evidence_ids = tuple(normalize_text(value) for value in evidence if normalize_text(value)) if isinstance(evidence, Sequence) else ()
            explicit = item.get("compatibility_score")
            if explicit is None:
                if item.get("supports_prediction") is True:
                    explicit = 0.9
                elif item.get("contradicts_prediction") is True:
                    explicit = 0.1
            score = None if explicit is None else _clamp(explicit, 0.5)
            observation_id = normalize_text(item.get("id") or item.get("observation_id")) or deterministic_id(
                "scientific-observation", {"index": index, "text": text, "prediction_id": prediction_id}
            )
            result.append(ScientificObservation(
                observation_id=observation_id, text=text, prediction_id=prediction_id,
                evidence_ids=evidence_ids, compatibility_score=score,
                matches_falsification_condition=bool(item.get("matches_falsification_condition", False)),
                metadata=dict(item.get("metadata", {})) if isinstance(item.get("metadata"), Mapping) else {},
            ))
        return result

    @staticmethod
    def _verify(prediction, observations: list[ScientificObservation]) -> VerificationReport:
        linked = [item for item in observations if item.prediction_id in {None, prediction.prediction_id}]
        scored = [item.compatibility_score for item in linked if item.compatibility_score is not None]
        limitations: tuple[str, ...]
        if not linked:
            status, consistency, evidence, rationale = VerificationStatus.UNTESTED, 0.0, 0.0, "Aucune observation liée à la prédiction."
            limitations = ("La prédiction reste non testée.",)
        elif not scored:
            status, consistency, evidence, rationale = VerificationStatus.INCONCLUSIVE, 0.5, min(1.0, len(linked) / 3), "Des observations existent, mais leur compatibilité n'est pas qualifiée."
            limitations = ("Un score de compatibilité explicite est requis.",)
        else:
            consistency = round(sum(scored) / len(scored), 6)
            evidence = round(min(1.0, (len(scored) / max(1, len(linked))) * min(1.0, len(linked) / 2)), 6)
            if consistency >= 0.75:
                status = VerificationStatus.CONFIRMED
            elif consistency >= 0.4:
                status = VerificationStatus.WEAKENED
            else:
                status = VerificationStatus.CONTRADICTED
            rationale = f"Compatibilité moyenne de {consistency:.2f} sur {len(scored)} observation(s) qualifiée(s)."
            limitations = () if len(scored) == len(linked) else ("Certaines observations ne sont pas qualifiées.",)
        report_id = deterministic_id("verification-report", {"prediction": prediction.prediction_id, "observations": [i.observation_id for i in linked], "status": status.value})
        return VerificationReport(report_id=report_id, prediction_id=prediction.prediction_id, observation_ids=tuple(i.observation_id for i in linked), status=status, consistency_score=consistency, evidence_score=evidence, rationale=rationale, limitations=limitations)


class FalsificationEngine:
    stage = ReasoningStage.FALSIFICATION

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        predictions = {item.prediction_id: item for item in state.scientific_predictions}
        observations = {item.observation_id: item for item in state.scientific_observations}
        reports = []
        revisions = []
        for verification in state.verification_reports:
            prediction = predictions[verification.prediction_id]
            linked = [observations[item] for item in verification.observation_ids if item in observations]
            formal = bool(prediction.falsification_condition)
            condition_met = any(item.matches_falsification_condition for item in linked)
            falsified = formal and verification.status is VerificationStatus.CONTRADICTED and (condition_met or verification.consistency_score <= 0.2)
            revision_required = falsified
            rationale = (
                "La condition de falsification est satisfaite par des observations contradictoires."
                if falsified else
                "La prédiction est contredite, mais aucune falsification formelle ne peut être conclue."
                if verification.status is VerificationStatus.CONTRADICTED else
                "Les observations disponibles ne falsifient pas la prédiction."
            )
            report = FalsificationReport(
                report_id=deterministic_id("falsification-report", {"verification": verification.report_id, "falsified": falsified}),
                prediction_id=prediction.prediction_id, verification_report_id=verification.report_id,
                falsified=falsified, formal_test_possible=formal,
                falsification_condition_met=condition_met, revision_required=revision_required,
                affected_claim_ids=prediction.source_claim_ids, rationale=rationale,
            )
            reports.append(report)
            action = "revise" if falsified else "retain" if verification.status is VerificationStatus.CONFIRMED else "review"
            revisions.append(ScientificTheoryRevision(
                revision_id=deterministic_id("scientific-theory-revision", {"prediction": prediction.prediction_id, "action": action, "verification": verification.report_id}),
                prediction_id=prediction.prediction_id, action=action,
                affected_claim_ids=prediction.source_claim_ids, reason=rationale,
            ))
        state.falsification_reports = reports
        state.scientific_theory_revisions = revisions
        return {
            "falsification_reports": [item.to_dict() for item in reports],
            "scientific_theory_revisions": [item.to_dict() for item in revisions],
        }
