from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState, normalize_text
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
    PredictionConfidenceLevel,
    ScenarioSimulation,
    ScientificGap,
    ScientificPrediction,
    ScientificScenario,
    TheoryClaim,
    TheoryClaimStatus,
    TheoryComparison,
    TheoryEvolution,
    TheoryGraph,
    TheoryHistory,
    TheoryMaturity,
    TheoryProposition,
    TheoryPropositionRole,
    TheorySnapshot,
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

        history_payload = state.conversation_context.get("theory_history")
        history_payload = history_payload if isinstance(history_payload, Mapping) else {}
        raw_snapshots = _items(history_payload.get("snapshots"))
        snapshots: list[TheorySnapshot] = []
        for index, raw_snapshot in enumerate(raw_snapshots, start=1):
            raw_propositions = _items(raw_snapshot.get("propositions") or raw_snapshot.get("claims"))
            propositions: list[TheoryProposition] = []
            for p_index, item in enumerate(raw_propositions, start=1):
                text = normalize_text(item.get("text"))
                if not text:
                    continue
                status = _claim_status(item.get("status"), ())
                role_text = normalize_text(item.get("role")).casefold()
                role = {r.value: r for r in TheoryPropositionRole}.get(role_text, TheoryPropositionRole.PROPOSITION)
                confidence = item.get("confidence")
                confidence = float(confidence) if isinstance(confidence, (int, float)) else 0.0
                propositions.append(TheoryProposition(
                    proposition_id=normalize_text(item.get("proposition_id") or item.get("id")) or f"snapshot-{index}-p{p_index}",
                    text=text, role=role, status=status, confidence=max(0.0, min(1.0, confidence)),
                ))
            maturity_payload = raw_snapshot.get("maturity")
            maturity_payload = maturity_payload if isinstance(maturity_payload, Mapping) else {}
            snapshots.append(TheorySnapshot(
                snapshot_id=normalize_text(raw_snapshot.get("snapshot_id") or raw_snapshot.get("id")) or f"snapshot-{index}",
                theory_id=normalize_text(raw_snapshot.get("theory_id")) or state.theory.theory_id,
                version=normalize_text(raw_snapshot.get("version")) or f"0.{index}",
                propositions=tuple(propositions),
                maturity=TheoryMaturity(
                    score=float(maturity_payload.get("score", 0.0) or 0.0),
                    level=normalize_text(maturity_payload.get("level")) or "embryonic",
                    supported_ratio=float(maturity_payload.get("supported_ratio", 0.0) or 0.0),
                    evidence_coverage=float(maturity_payload.get("evidence_coverage", 0.0) or 0.0),
                    contradiction_ratio=float(maturity_payload.get("contradiction_ratio", 0.0) or 0.0),
                ),
                parent_snapshot_id=normalize_text(raw_snapshot.get("parent_snapshot_id")) or None,
                change_summary=normalize_text(raw_snapshot.get("change_summary")),
            ))

        explicit_version = normalize_text(state.conversation_context.get("theory_version"))
        if explicit_version:
            next_version = explicit_version
        elif snapshots:
            last = snapshots[-1].version
            parts = last.split(".")
            if parts and parts[-1].isdigit():
                parts[-1] = str(int(parts[-1]) + 1)
                next_version = ".".join(parts)
            else:
                next_version = f"{last}.1"
        else:
            next_version = "1.0"

        change_count = len(added) + len(removed) + len(strengthened) + len(weakened)
        summary = (
            f"{len(added)} ajout(s), {len(removed)} retrait(s), "
            f"{len(strengthened)} renforcement(s), {len(weakened)} affaiblissement(s)."
        )
        parent_id = snapshots[-1].snapshot_id if snapshots else None
        current_snapshot = TheorySnapshot(
            snapshot_id=f"{state.theory.theory_id}@{next_version}",
            theory_id=state.theory.theory_id,
            version=next_version,
            propositions=state.theory.propositions,
            maturity=state.theory.maturity,
            parent_snapshot_id=parent_id,
            change_summary=summary if change_count else "Aucun changement structurel détecté.",
        )
        if not snapshots or snapshots[-1].to_dict() != current_snapshot.to_dict():
            snapshots.append(current_snapshot)
        state.theory_history = TheoryHistory(
            theory_id=state.theory.theory_id,
            snapshots=tuple(snapshots),
            current_snapshot_id=current_snapshot.snapshot_id,
        )
        return {
            "theory_evolution": state.theory_evolution.to_dict(),
            "theory_history": state.theory_history.to_dict(),
            "current_snapshot": current_snapshot.to_dict(),
        }


class PredictionEngine:
    stage = ReasoningStage.PREDICTION

    _STATUS_BASE = {
        TheoryClaimStatus.SUPPORTED: 0.82,
        TheoryClaimStatus.PARTIAL: 0.58,
        TheoryClaimStatus.UNSUPPORTED: 0.28,
        TheoryClaimStatus.CONTRADICTED: 0.05,
    }

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        predictions = self._build_predictions(state)
        scenarios = self._build_scenarios(state)
        simulations = self._simulate(predictions, scenarios)

        state.scientific_predictions = predictions
        state.scientific_scenarios = scenarios
        state.scenario_simulations = simulations
        return {
            "scientific_predictions": [item.to_dict() for item in predictions],
            "scientific_scenarios": [item.to_dict() for item in scenarios],
            "scenario_simulations": [item.to_dict() for item in simulations],
        }

    def _build_predictions(self, state: ReasoningExecutionState) -> list[ScientificPrediction]:
        predictions: list[ScientificPrediction] = []
        raw_predictions = list(_items(state.conversation_context.get("predictions", ())))
        raw_predictions.extend(self._rules_as_predictions(state.conversation_context.get("prediction_rules", ())))
        claims = {claim.claim_id: claim for claim in state.theory_graph.claims}

        for index, item in enumerate(raw_predictions, start=1):
            text = normalize_text(item.get("text"))
            if not text:
                continue
            source_ids = item.get("source_claim_ids", ())
            source_ids = tuple(
                normalize_text(value) for value in source_ids if normalize_text(value)
            ) if isinstance(source_ids, (list, tuple)) else ()
            assumptions = item.get("assumptions", ())
            assumptions = tuple(
                normalize_text(value) for value in assumptions if normalize_text(value)
            ) if isinstance(assumptions, (list, tuple)) else ()
            falsification = normalize_text(item.get("falsification_condition")) or None
            expected = normalize_text(item.get("expected_observation")) or None
            confidence, factors = self._confidence(
                item=item,
                source_ids=source_ids,
                claims=claims,
                maturity=state.theory.maturity.score,
                falsification_condition=falsification,
                expected_observation=expected,
                assumptions=assumptions,
            )
            predictions.append(ScientificPrediction(
                prediction_id=normalize_text(item.get("id") or item.get("prediction_id")) or f"prediction-{index}",
                text=text,
                source_claim_ids=source_ids,
                falsification_condition=falsification,
                status=normalize_text(item.get("status")) or "untested",
                confidence=confidence,
                confidence_level=self._confidence_level(confidence),
                confidence_factors=factors,
                assumptions=assumptions,
                expected_observation=expected,
                horizon=normalize_text(item.get("horizon")) or None,
            ))
        return predictions

    @staticmethod
    def _rules_as_predictions(value: Any) -> list[Mapping[str, Any]]:
        results: list[Mapping[str, Any]] = []
        for index, rule in enumerate(_items(value), start=1):
            condition = normalize_text(rule.get("if") or rule.get("condition"))
            consequence = normalize_text(rule.get("then") or rule.get("consequence"))
            if not condition or not consequence:
                continue
            payload = dict(rule)
            payload.setdefault("id", f"prediction-rule-{index}")
            payload["text"] = f"Si {condition}, alors {consequence}."
            assumptions = list(payload.get("assumptions", ())) if isinstance(payload.get("assumptions"), (list, tuple)) else []
            if condition not in assumptions:
                assumptions.append(condition)
            payload["assumptions"] = assumptions
            results.append(payload)
        return results

    def _confidence(
        self,
        *,
        item: Mapping[str, Any],
        source_ids: tuple[str, ...],
        claims: Mapping[str, TheoryClaim],
        maturity: float,
        falsification_condition: str | None,
        expected_observation: str | None,
        assumptions: tuple[str, ...],
    ) -> tuple[float, tuple[str, ...]]:
        explicit = item.get("confidence")
        if isinstance(explicit, (int, float)):
            value = self._clamp(float(explicit))
            return value, ("confiance fournie explicitement",)

        factors: list[str] = []
        source_scores: list[float] = []
        for source_id in source_ids:
            claim = claims.get(source_id)
            if claim is None:
                factors.append(f"source inconnue : {source_id}")
                source_scores.append(0.20)
                continue
            score = self._STATUS_BASE[claim.status]
            if claim.evidence:
                score = min(1.0, score + min(0.10, len(claim.evidence) * 0.04))
                factors.append(f"preuve associée à {source_id}")
            factors.append(f"statut {claim.status.value} pour {source_id}")
            source_scores.append(score)

        source_score = sum(source_scores) / len(source_scores) if source_scores else 0.25
        maturity_score = self._clamp(float(maturity or 0.0))
        confidence = (0.75 * source_score) + (0.25 * maturity_score)
        factors.append(f"maturité de théorie : {maturity_score:.2f}")
        if falsification_condition:
            confidence += 0.05
            factors.append("condition de falsification explicite")
        if expected_observation:
            confidence += 0.05
            factors.append("observation attendue explicite")
        if assumptions:
            confidence -= min(0.15, len(assumptions) * 0.03)
            factors.append(f"{len(assumptions)} hypothèse(s) conditionnelle(s)")
        return round(self._clamp(confidence), 4), tuple(factors)

    @staticmethod
    def _confidence_level(value: float) -> PredictionConfidenceLevel:
        if value < 0.20:
            return PredictionConfidenceLevel.VERY_LOW
        if value < 0.40:
            return PredictionConfidenceLevel.LOW
        if value < 0.65:
            return PredictionConfidenceLevel.MODERATE
        if value < 0.85:
            return PredictionConfidenceLevel.HIGH
        return PredictionConfidenceLevel.VERY_HIGH

    @staticmethod
    def _build_scenarios(state: ReasoningExecutionState) -> list[ScientificScenario]:
        scenarios: list[ScientificScenario] = []
        for index, item in enumerate(_items(state.conversation_context.get("scenarios", ())), start=1):
            name = normalize_text(item.get("name")) or f"Scénario {index}"
            assumptions = item.get("assumptions", ())
            assumptions = tuple(
                normalize_text(value) for value in assumptions if normalize_text(value)
            ) if isinstance(assumptions, (list, tuple)) else ()
            variables = item.get("variables")
            variables = dict(variables) if isinstance(variables, Mapping) else {}
            scenarios.append(ScientificScenario(
                scenario_id=normalize_text(item.get("id") or item.get("scenario_id")) or f"scenario-{index}",
                name=name,
                description=normalize_text(item.get("description")),
                assumptions=assumptions,
                variables=variables,
            ))
        return scenarios

    def _simulate(
        self,
        predictions: list[ScientificPrediction],
        scenarios: list[ScientificScenario],
    ) -> list[ScenarioSimulation]:
        simulations: list[ScenarioSimulation] = []
        for scenario in scenarios:
            scenario_assumptions = {item.casefold(): item for item in scenario.assumptions}
            modifier = scenario.variables.get("confidence_modifier", 0.0)
            modifier = float(modifier) if isinstance(modifier, (int, float)) else 0.0
            for prediction in predictions:
                matched = tuple(
                    assumption for assumption in prediction.assumptions
                    if assumption.casefold() in scenario_assumptions
                )
                missing = tuple(
                    assumption for assumption in prediction.assumptions
                    if assumption.casefold() not in scenario_assumptions
                )
                if not prediction.assumptions:
                    outcome = "applicable"
                    rationale = "La prédiction ne déclare aucune hypothèse de scénario obligatoire."
                    assumption_adjustment = 0.0
                elif missing:
                    outcome = "conditional"
                    rationale = "Le scénario ne satisfait pas toutes les hypothèses déclarées."
                    assumption_adjustment = -min(0.30, len(missing) * 0.10)
                else:
                    outcome = "supported_by_scenario"
                    rationale = "Le scénario satisfait toutes les hypothèses déclarées."
                    assumption_adjustment = min(0.12, len(matched) * 0.04)
                adjusted = round(self._clamp(prediction.confidence + assumption_adjustment + modifier), 4)
                simulations.append(ScenarioSimulation(
                    simulation_id=f"{scenario.scenario_id}:{prediction.prediction_id}",
                    scenario_id=scenario.scenario_id,
                    prediction_id=prediction.prediction_id,
                    outcome=outcome,
                    adjusted_confidence=adjusted,
                    matched_assumptions=matched,
                    missing_assumptions=missing,
                    rationale=rationale,
                ))
        return simulations

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))


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
