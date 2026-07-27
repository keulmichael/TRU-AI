from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState, normalize_text
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
    ScientificGap,
    ScientificPrediction,
    TheoryClaim,
    TheoryClaimStatus,
    TheoryComparison,
    TheoryEvolution,
    TheoryGraph,
    TruthStatus,
)


def _items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _claim_status(value: Any, evidence: tuple[str, ...]) -> TheoryClaimStatus:
    normalized = normalize_text(value).casefold()
    aliases = {
        "supported": TheoryClaimStatus.SUPPORTED,
        "partial": TheoryClaimStatus.PARTIAL,
        "unsupported": TheoryClaimStatus.UNSUPPORTED,
        "contradicted": TheoryClaimStatus.CONTRADICTED,
    }
    if normalized in aliases:
        return aliases[normalized]
    return TheoryClaimStatus.SUPPORTED if evidence else TheoryClaimStatus.UNSUPPORTED


def _normalize_claim_text(text: str) -> str:
    return normalize_text(text).casefold().rstrip(" .;:!?")


def _is_negation_pair(left: str, right: str) -> bool:
    left_n = _normalize_claim_text(left)
    right_n = _normalize_claim_text(right)
    prefixes = ("ne ", "n'", "not ", "non ")
    for prefix in prefixes:
        if left_n.startswith(prefix) and left_n[len(prefix):] == right_n:
            return True
        if right_n.startswith(prefix) and right_n[len(prefix):] == left_n:
            return True
    return False


class TheoryConstructionEngine:
    stage = ReasoningStage.THEORY_CONSTRUCTION

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        raw = state.conversation_context.get("theory")
        if not isinstance(raw, Mapping):
            raw = state.conversation_context.get("theory_graph")
        raw = raw if isinstance(raw, Mapping) else {}

        claims: list[TheoryClaim] = []
        for index, item in enumerate(_items(raw.get("claims")), start=1):
            text = normalize_text(item.get("text"))
            if not text:
                continue
            evidence = tuple(
                normalize_text(value)
                for value in item.get("evidence", ())
                if normalize_text(value)
            ) if isinstance(item.get("evidence", ()), (list, tuple)) else ()
            limitations = tuple(
                normalize_text(value)
                for value in item.get("limitations", ())
                if normalize_text(value)
            ) if isinstance(item.get("limitations", ()), (list, tuple)) else ()
            confidence = item.get("confidence")
            confidence = float(confidence) if isinstance(confidence, (int, float)) else None
            claims.append(TheoryClaim(
                claim_id=normalize_text(item.get("id") or item.get("claim_id")) or f"theory-claim-{index}",
                text=text,
                status=_claim_status(item.get("status"), evidence),
                evidence=evidence,
                limitations=limitations,
                confidence=confidence,
            ))

        if not claims:
            for index, claim in enumerate(state.claims, start=1):
                evidence = tuple(claim.support)
                status = (
                    TheoryClaimStatus.SUPPORTED
                    if claim.status in (TruthStatus.EXPLICIT, TruthStatus.DEDUCTION)
                    else TheoryClaimStatus.PARTIAL
                )
                claims.append(TheoryClaim(
                    claim_id=f"reasoning-claim-{index}",
                    text=claim.text,
                    status=status,
                    evidence=evidence,
                    limitations=tuple(claim.limitations),
                    confidence=claim.confidence,
                ))

        relations: list[tuple[str, str, str]] = []
        for item in _items(raw.get("relations")):
            source = normalize_text(item.get("source") or item.get("source_id"))
            target = normalize_text(item.get("target") or item.get("target_id"))
            relation = normalize_text(item.get("type") or item.get("relation_type")) or "supports"
            if source and target:
                relations.append((source, target, relation))

        state.theory_graph = TheoryGraph(
            theory_id=normalize_text(raw.get("id") or raw.get("theory_id")) or "current-theory",
            name=normalize_text(raw.get("name")) or "Théorie courante",
            claims=tuple(claims),
            relations=tuple(relations),
        )
        return {"theory_graph": state.theory_graph.to_dict()}


class TheoryComparisonEngine:
    stage = ReasoningStage.THEORY_COMPARISON

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        current = {_normalize_claim_text(item.text): item.text for item in state.theory_graph.claims}
        comparisons: list[TheoryComparison] = []
        for index, theory in enumerate(_items(state.conversation_context.get("comparison_theories")), start=1):
            compared_claims = [normalize_text(item.get("text")) for item in _items(theory.get("claims"))]
            compared = {_normalize_claim_text(text): text for text in compared_claims if text}
            shared = tuple(sorted(current[key] for key in current.keys() & compared.keys()))
            current_only = tuple(sorted(current[key] for key in current.keys() - compared.keys()))
            compared_only = tuple(sorted(compared[key] for key in compared.keys() - current.keys()))
            contradictions = tuple(sorted(
                f"{left} ↔ {right}"
                for left in current_only
                for right in compared_only
                if _is_negation_pair(left, right)
            ))
            comparisons.append(TheoryComparison(
                compared_theory_id=normalize_text(theory.get("id") or theory.get("theory_id")) or f"compared-theory-{index}",
                compared_theory_name=normalize_text(theory.get("name")) or f"Théorie comparée {index}",
                shared_claims=shared,
                current_only_claims=current_only,
                compared_only_claims=compared_only,
                contradictions=contradictions,
            ))
        state.theory_comparisons = comparisons
        return {"theory_comparisons": [item.to_dict() for item in comparisons]}


class TheoryEvolutionEngine:
    stage = ReasoningStage.THEORY_EVOLUTION

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        baseline = state.conversation_context.get("baseline_theory")
        baseline = baseline if isinstance(baseline, Mapping) else {}
        previous_items = _items(baseline.get("claims"))
        previous = {_normalize_claim_text(normalize_text(item.get("text"))): item for item in previous_items if normalize_text(item.get("text"))}
        current = {_normalize_claim_text(item.text): item for item in state.theory_graph.claims}

        added = tuple(sorted(current[key].text for key in current.keys() - previous.keys()))
        removed = tuple(sorted(normalize_text(previous[key].get("text")) for key in previous.keys() - current.keys()))
        strengthened: list[str] = []
        weakened: list[str] = []
        rank = {"unsupported": 0, "partial": 1, "supported": 2, "contradicted": -1}
        for key in current.keys() & previous.keys():
            old = normalize_text(previous[key].get("status")).casefold() or "unsupported"
            new = current[key].status.value
            if rank.get(new, 0) > rank.get(old, 0):
                strengthened.append(current[key].text)
            elif rank.get(new, 0) < rank.get(old, 0):
                weakened.append(current[key].text)

        state.theory_evolution = TheoryEvolution(
            added_claims=added,
            removed_claims=removed,
            strengthened_claims=tuple(sorted(strengthened)),
            weakened_claims=tuple(sorted(weakened)),
        )
        return {"theory_evolution": state.theory_evolution.to_dict()}


class PredictionEngine:
    stage = ReasoningStage.PREDICTION

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        predictions: list[ScientificPrediction] = []
        raw_predictions = state.conversation_context.get("predictions", ())
        for index, item in enumerate(_items(raw_predictions), start=1):
            text = normalize_text(item.get("text"))
            if not text:
                continue
            source_ids = item.get("source_claim_ids", ())
            source_ids = tuple(normalize_text(value) for value in source_ids if normalize_text(value)) if isinstance(source_ids, (list, tuple)) else ()
            predictions.append(ScientificPrediction(
                prediction_id=normalize_text(item.get("id") or item.get("prediction_id")) or f"prediction-{index}",
                text=text,
                source_claim_ids=source_ids,
                falsification_condition=normalize_text(item.get("falsification_condition")) or None,
                status=normalize_text(item.get("status")) or "untested",
            ))
        state.scientific_predictions = predictions
        return {"scientific_predictions": [item.to_dict() for item in predictions]}


class ScientificGapEngine:
    stage = ReasoningStage.SCIENTIFIC_GAPS

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        gaps: list[ScientificGap] = []
        for claim in state.theory_graph.claims:
            if not claim.evidence:
                gaps.append(ScientificGap(
                    gap_id=f"missing-evidence-{claim.claim_id}",
                    description=f"Aucune preuve n'est associée à la proposition : {claim.text}",
                    related_claim_ids=(claim.claim_id,),
                    required_action="Fournir une observation, une source ou un résultat expérimental.",
                ))
        for index, item in enumerate(_items(state.conversation_context.get("scientific_gaps")), start=1):
            description = normalize_text(item.get("description"))
            if description:
                related = item.get("related_claim_ids", ())
                related = tuple(normalize_text(value) for value in related if normalize_text(value)) if isinstance(related, (list, tuple)) else ()
                gaps.append(ScientificGap(
                    gap_id=normalize_text(item.get("id") or item.get("gap_id")) or f"scientific-gap-{index}",
                    description=description,
                    gap_type=normalize_text(item.get("type") or item.get("gap_type")) or "missing_evidence",
                    related_claim_ids=related,
                    required_action=normalize_text(item.get("required_action")) or None,
                ))
        state.scientific_gaps = gaps
        return {"scientific_gaps": [item.to_dict() for item in gaps]}
