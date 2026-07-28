from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState, normalize_text
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
    Theory,
    TheoryClaim,
    TheoryClaimStatus,
    TheoryEvidence,
    TheoryGraph,
    TheoryMaturity,
    TheoryProposition,
    TheoryPropositionRole,
    TheoryRevision,
    TruthStatus,
)


def _items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _key(text: str) -> str:
    return normalize_text(text).casefold().rstrip(" .;:!?")


def _unique(values: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return tuple(result)


def _status(value: Any, evidence_count: int) -> TheoryClaimStatus:
    aliases = {item.value: item for item in TheoryClaimStatus}
    normalized = normalize_text(value).casefold()
    return aliases.get(normalized, TheoryClaimStatus.SUPPORTED if evidence_count else TheoryClaimStatus.UNSUPPORTED)


def _role(value: Any, status: TheoryClaimStatus, evidence_count: int, confidence: float) -> TheoryPropositionRole:
    normalized = normalize_text(value).casefold()
    aliases = {item.value: item for item in TheoryPropositionRole}
    if normalized in aliases:
        return aliases[normalized]
    if status is TheoryClaimStatus.SUPPORTED and evidence_count >= 2 and confidence >= 0.85:
        return TheoryPropositionRole.AXIOM
    if status in (TheoryClaimStatus.PARTIAL, TheoryClaimStatus.UNSUPPORTED):
        return TheoryPropositionRole.HYPOTHESIS
    return TheoryPropositionRole.PROPOSITION


class TheoryBuilderEngine:
    """Construit une théorie déterministe, dédupliquée et mesurable."""

    stage = ReasoningStage.THEORY_CONSTRUCTION

    def execute(self, *, step: ReasoningStep, state: ReasoningExecutionState) -> Mapping[str, Any]:
        raw = state.conversation_context.get("theory")
        if not isinstance(raw, Mapping):
            raw = state.conversation_context.get("theory_graph")
        raw = raw if isinstance(raw, Mapping) else {}

        candidates: list[dict[str, Any]] = []
        for index, item in enumerate(_items(raw.get("claims") or raw.get("propositions")), start=1):
            text = normalize_text(item.get("text"))
            if not text:
                continue
            ev = item.get("evidence", ())
            evidence = _unique(ev if isinstance(ev, (list, tuple)) else ())
            confidence = float(item.get("confidence")) if isinstance(item.get("confidence"), (int, float)) else (0.75 if evidence else 0.25)
            candidates.append({
                "id": normalize_text(item.get("id") or item.get("claim_id") or item.get("proposition_id")) or f"theory-claim-{index}",
                "text": text,
                "status": _status(item.get("status"), len(evidence)),
                "role": item.get("role"),
                "evidence": evidence,
                "limitations": _unique(item.get("limitations", ()) if isinstance(item.get("limitations", ()), (list, tuple)) else ()),
                "confidence": max(0.0, min(1.0, confidence)),
            })

        if not candidates:
            for index, claim in enumerate(state.claims, start=1):
                status = TheoryClaimStatus.SUPPORTED if claim.status in (TruthStatus.EXPLICIT, TruthStatus.DEDUCTION) else TheoryClaimStatus.PARTIAL
                candidates.append({
                    "id": f"reasoning-claim-{index}", "text": claim.text, "status": status,
                    "role": "hypothesis" if claim.status is TruthStatus.HYPOTHESIS else None,
                    "evidence": tuple(claim.support), "limitations": tuple(claim.limitations),
                    "confidence": claim.confidence if claim.confidence is not None else (0.7 if status is TheoryClaimStatus.SUPPORTED else 0.4),
                })

        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in candidates:
            grouped.setdefault(_key(item["text"]), []).append(item)

        evidence_objects: list[TheoryEvidence] = []
        propositions: list[TheoryProposition] = []
        revisions: list[TheoryRevision] = []
        graph_claims: list[TheoryClaim] = []

        for number, group in enumerate(grouped.values(), start=1):
            primary = group[0]
            evidence_texts = _unique([e for item in group for e in item["evidence"]])
            evidence_ids: list[str] = []
            for text in evidence_texts:
                evidence_id = f"evidence-{len(evidence_objects)+1}"
                evidence_objects.append(TheoryEvidence(evidence_id=evidence_id, description=text))
                evidence_ids.append(evidence_id)
            confidence = round(sum(float(item["confidence"]) for item in group) / len(group), 4)
            statuses = [item["status"] for item in group]
            status = TheoryClaimStatus.CONTRADICTED if TheoryClaimStatus.CONTRADICTED in statuses else max(statuses, key=lambda value: {TheoryClaimStatus.UNSUPPORTED:0, TheoryClaimStatus.PARTIAL:1, TheoryClaimStatus.SUPPORTED:2}.get(value, -1))
            proposition_id = primary["id"]
            role = _role(primary.get("role"), status, len(evidence_ids), confidence)
            limitations = _unique([x for item in group for x in item["limitations"]])
            source_ids = _unique([item["id"] for item in group])
            propositions.append(TheoryProposition(proposition_id=proposition_id, text=primary["text"], role=role, status=status, evidence_ids=tuple(evidence_ids), limitations=limitations, confidence=confidence, source_claim_ids=source_ids))
            graph_claims.append(TheoryClaim(claim_id=proposition_id, text=primary["text"], status=status, evidence=evidence_texts, limitations=limitations, confidence=confidence))
            if len(group) > 1:
                revisions.append(TheoryRevision(revision_id=f"revision-{number}", action="merged", proposition_id=proposition_id, description=f"{len(group)} formulations équivalentes ont été fusionnées."))
            if role is TheoryPropositionRole.AXIOM:
                revisions.append(TheoryRevision(revision_id=f"promotion-{number}", action="promoted_to_axiom", proposition_id=proposition_id, description="La proposition satisfait les seuils déterministes de corroboration."))

        total = len(propositions)
        supported = sum(p.status is TheoryClaimStatus.SUPPORTED for p in propositions)
        contradicted = sum(p.status is TheoryClaimStatus.CONTRADICTED for p in propositions)
        covered = sum(bool(p.evidence_ids) for p in propositions)
        supported_ratio = supported / total if total else 0.0
        evidence_coverage = covered / total if total else 0.0
        contradiction_ratio = contradicted / total if total else 0.0
        score = round(max(0.0, min(1.0, 0.55 * supported_ratio + 0.35 * evidence_coverage + 0.10 * (1.0 - contradiction_ratio))), 4) if total else 0.0
        level = "mature" if score >= 0.8 else "developing" if score >= 0.5 else "embryonic"
        maturity = TheoryMaturity(score=score, level=level, supported_ratio=round(supported_ratio,4), evidence_coverage=round(evidence_coverage,4), contradiction_ratio=round(contradiction_ratio,4))

        theory_id = normalize_text(raw.get("id") or raw.get("theory_id")) or "current-theory"
        title = normalize_text(raw.get("name") or raw.get("title")) or "Théorie courante"
        state.theory = Theory(theory_id=theory_id, title=title, domain=normalize_text(raw.get("domain")) or None, propositions=tuple(propositions), evidence=tuple(evidence_objects), revisions=tuple(revisions), contradictions=tuple(state.contradictions), maturity=maturity)
        state.theory_graph = TheoryGraph(theory_id=theory_id, name=title, claims=tuple(graph_claims), relations=())
        return {"theory": state.theory.to_dict(), "theory_graph": state.theory_graph.to_dict()}


TheoryConstructionEngine = TheoryBuilderEngine
