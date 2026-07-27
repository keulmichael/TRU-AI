from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


CLASSIFICATIONS = (
    "EXPLICITE",
    "DÉDUCTION",
    "HYPOTHÈSE",
    "INCONNU",
)


def canonical_json(payload: dict) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def deterministic_id(prefix: str, payload: dict) -> str:
    digest = hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()[:16]
    return f"{prefix}-{digest}"


@dataclass(frozen=True)
class CognitiveClaim:
    claim_id: str
    classification: str
    text: str
    evidence_ids: tuple[str, ...]
    confidence: float
    premises: tuple[str, ...] = ()
    rule: str | None = None
    conclusion: str | None = None
    limitations: tuple[str, ...] = ()
    validity_score: float | None = None

    def to_dict(self) -> dict:
        data = {
            "claim_id": self.claim_id,
            "classification": self.classification,
            "text": self.text,
            "evidence_ids": sorted(self.evidence_ids),
            "confidence": round(self.confidence, 6),
            "premises": sorted(self.premises),
            "rule": self.rule,
            "conclusion": self.conclusion,
            "limitations": sorted(self.limitations),
        }
        if self.validity_score is not None:
            data["validity_score"] = round(self.validity_score, 6)
        return data


@dataclass(frozen=True)
class CognitiveEvidence:
    evidence_id: str
    element_id: str
    element_type: str
    text: str
    source_id: str
    document_id: str
    page_numbers: tuple[int, ...]
    relevance: float
    extraction_confidence: float = 1.0
    semantic_validation_status: str = "CONFIRMÉ"
    semantic_justification: str = ""
    authority: float = 0.75
    conceptual_proximity: float = 0.75
    directness: float = 0.75
    completeness: float = 0.75
    context_loss_risk: float = 0.25
    redundancy: float = 0.0

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "text": self.text,
            "source_id": self.source_id,
            "document_id": self.document_id,
            "page_numbers": sorted(self.page_numbers),
            "relevance": round(self.relevance, 6),
            "extraction_confidence": round(
                self.extraction_confidence,
                6,
            ),
            "semantic_validation_status": self.semantic_validation_status,
            "semantic_justification": self.semantic_justification,
            "authority": round(self.authority, 6),
            "conceptual_proximity": round(self.conceptual_proximity, 6),
            "directness": round(self.directness, 6),
            "completeness": round(self.completeness, 6),
            "context_loss_risk": round(self.context_loss_risk, 6),
            "redundancy": round(self.redundancy, 6),
        }


@dataclass(frozen=True)
class CognitiveComparison:
    comparison_id: str
    compared_states: tuple[str, ...]
    provenance: tuple[str, ...]
    dimensions: tuple[str, ...]
    similarities: tuple[str, ...]
    differences: tuple[str, ...]
    delta_detected: str | None
    tru_meaning: str | None
    limitations: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "comparison_id": self.comparison_id,
            "compared_states": list(self.compared_states),
            "provenance": sorted(self.provenance),
            "dimensions": sorted(self.dimensions),
            "similarities": sorted(self.similarities),
            "differences": sorted(self.differences),
            "delta_detected": self.delta_detected,
            "tru_meaning": self.tru_meaning,
            "limitations": sorted(self.limitations),
        }


@dataclass(frozen=True)
class TruOperator:
    operator_id: str
    name: str
    definitions: tuple[str, ...]
    inputs: tuple[str, ...]
    preconditions: tuple[str, ...]
    transformation: str
    outputs: tuple[str, ...]
    limitations: tuple[str, ...]
    source_evidence: tuple[str, ...]
    conceptual_version: str

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "name": self.name,
            "definitions": sorted(self.definitions),
            "inputs": list(self.inputs),
            "preconditions": list(self.preconditions),
            "transformation": self.transformation,
            "outputs": list(self.outputs),
            "limitations": sorted(self.limitations),
            "source_evidence": sorted(self.source_evidence),
            "conceptual_version": self.conceptual_version,
        }


@dataclass(frozen=True)
class OperatorApplication:
    application_id: str
    operator_id: str
    applied: bool
    refusal_reason: str | None
    premise_evidence_ids: tuple[str, ...]
    rule: str
    output: str | None
    confidence: float

    def to_dict(self) -> dict:
        return {
            "application_id": self.application_id,
            "operator_id": self.operator_id,
            "applied": self.applied,
            "refusal_reason": self.refusal_reason,
            "premise_evidence_ids": sorted(self.premise_evidence_ids),
            "rule": self.rule,
            "output": self.output,
            "confidence": round(self.confidence, 6),
        }


@dataclass(frozen=True)
class CognitiveAnswer:
    summary: str
    explicit_claims: tuple[CognitiveClaim, ...]
    deductions: tuple[CognitiveClaim, ...]
    hypotheses: tuple[CognitiveClaim, ...]
    unknowns: tuple[CognitiveClaim, ...]
    sources: tuple[dict, ...]
    missing_knowledge: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "explicit_claims": [
                claim.to_dict()
                for claim in self.explicit_claims
            ],
            "deductions": [
                claim.to_dict()
                for claim in self.deductions
            ],
            "hypotheses": [
                claim.to_dict()
                for claim in self.hypotheses
            ],
            "unknowns": [
                claim.to_dict()
                for claim in self.unknowns
            ],
            "sources": list(self.sources),
            "missing_knowledge": sorted(self.missing_knowledge),
            "warnings": sorted(self.warnings),
        }


@dataclass(frozen=True)
class CognitiveRequestTrace:
    request_id: str
    original_question: str
    intent: str
    detected_concepts: tuple[str, ...]
    selected_concepts: tuple[str, ...]
    sources_consulted: tuple[str, ...]
    pages_consulted: tuple[int, ...]
    chapters_consulted: tuple[str, ...]
    definitions_used: tuple[str, ...]
    axioms_used: tuple[str, ...]
    propositions_used: tuple[str, ...]
    demonstrations_used: tuple[str, ...]
    relations_used: tuple[str, ...]
    inferences_used: tuple[str, ...]
    evidence_used: tuple[str, ...]
    evidence_rejected: tuple[str, ...]
    response_plan: tuple[str, ...]
    explicit_claim_ids: tuple[str, ...]
    deduction_claim_ids: tuple[str, ...]
    hypothesis_claim_ids: tuple[str, ...]
    unknown_claim_ids: tuple[str, ...]
    contradictions: tuple[str, ...]
    missing_knowledge: tuple[str, ...]
    coverage_score: float
    confidence: float
    confidence_justification: str

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "original_question": self.original_question,
            "intent": self.intent,
            "detected_concepts": sorted(self.detected_concepts),
            "selected_concepts": sorted(self.selected_concepts),
            "sources_consulted": sorted(self.sources_consulted),
            "pages_consulted": sorted(self.pages_consulted),
            "chapters_consulted": sorted(self.chapters_consulted),
            "definitions_used": sorted(self.definitions_used),
            "axioms_used": sorted(self.axioms_used),
            "propositions_used": sorted(self.propositions_used),
            "demonstrations_used": sorted(self.demonstrations_used),
            "relations_used": sorted(self.relations_used),
            "inferences_used": sorted(self.inferences_used),
            "evidence_used": sorted(self.evidence_used),
            "evidence_rejected": sorted(self.evidence_rejected),
            "response_plan": list(self.response_plan),
            "explicit_claim_ids": sorted(self.explicit_claim_ids),
            "deduction_claim_ids": sorted(self.deduction_claim_ids),
            "hypothesis_claim_ids": sorted(self.hypothesis_claim_ids),
            "unknown_claim_ids": sorted(self.unknown_claim_ids),
            "contradictions": sorted(self.contradictions),
            "missing_knowledge": sorted(self.missing_knowledge),
            "coverage_score": round(self.coverage_score, 6),
            "confidence": round(self.confidence, 6),
            "confidence_justification": self.confidence_justification,
        }


@dataclass(frozen=True)
class CognitiveExecution:
    execution_id: str
    question: str
    context: tuple[str, ...]
    observation: str
    intention: str
    concepts_recognized: tuple[str, ...]
    concepts_rejected: tuple[str, ...]
    problem: str
    memory_activated: tuple[str, ...]
    evidence_selected: tuple[str, ...]
    comparisons: tuple[CognitiveComparison, ...]
    deltas_detected: tuple[str, ...]
    applicable_operators: tuple[TruOperator, ...]
    applied_operators: tuple[OperatorApplication, ...]
    premises: tuple[str, ...]
    rules: tuple[str, ...]
    deductions: tuple[str, ...]
    hypotheses: tuple[str, ...]
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    reflexive_evaluation: dict
    response_plan: tuple[str, ...]
    final_answer: str
    confidence: float
    confidence_justification: str

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "question": self.question,
            "context": list(self.context),
            "observation": self.observation,
            "intention": self.intention,
            "concepts_recognized": sorted(self.concepts_recognized),
            "concepts_rejected": sorted(self.concepts_rejected),
            "problem": self.problem,
            "memory_activated": sorted(self.memory_activated),
            "evidence_selected": sorted(self.evidence_selected),
            "comparisons": [
                comparison.to_dict()
                for comparison in self.comparisons
            ],
            "deltas_detected": sorted(self.deltas_detected),
            "applicable_operators": [
                operator.to_dict()
                for operator in self.applicable_operators
            ],
            "applied_operators": [
                application.to_dict()
                for application in self.applied_operators
            ],
            "premises": sorted(self.premises),
            "rules": sorted(self.rules),
            "deductions": sorted(self.deductions),
            "hypotheses": sorted(self.hypotheses),
            "unknowns": sorted(self.unknowns),
            "contradictions": sorted(self.contradictions),
            "reflexive_evaluation": dict(
                sorted(self.reflexive_evaluation.items())
            ),
            "response_plan": list(self.response_plan),
            "final_answer": self.final_answer,
            "confidence": round(self.confidence, 6),
            "confidence_justification": self.confidence_justification,
        }


@dataclass(frozen=True)
class CognitiveResponse:
    request_id: str
    answer: CognitiveAnswer
    confidence: float
    classifications: dict[str, list[dict]]
    sources: tuple[dict, ...]
    missing_knowledge: tuple[str, ...]
    warnings: tuple[str, ...]
    trace: CognitiveRequestTrace
    evidence: tuple[CognitiveEvidence, ...] = field(default_factory=tuple)
    execution: CognitiveExecution | None = None
    confidence_breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self, *, include_evidence: bool = True) -> dict:
        data = {
            "request_id": self.request_id,
            "answer": self.answer.to_dict(),
            "confidence": round(self.confidence, 6),
            "classifications": {
                key: list(value)
                for key, value in sorted(
                    self.classifications.items()
                )
            },
            "sources": list(self.sources),
            "missing_knowledge": sorted(self.missing_knowledge),
            "warnings": sorted(self.warnings),
            "confidence_breakdown": {
                key: round(value, 6)
                for key, value in sorted(self.confidence_breakdown.items())
            },
        }
        if self.execution is not None:
            data["cognitive_execution"] = self.execution.to_dict()
        if include_evidence:
            data["evidence"] = [
                evidence.to_dict()
                for evidence in self.evidence
            ]
        return data
