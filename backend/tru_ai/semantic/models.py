from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class MergeEvidence:
    evidence_type: str
    value: str
    weight: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class MergeDecision:
    source_node_id: str
    target_node_id: str
    decision: str
    confidence: float
    rule_id: str
    evidences: tuple[MergeEvidence, ...] = ()

    def to_dict(self) -> dict:
        return {
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "decision": self.decision,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            "evidences": [
                evidence.to_dict()
                for evidence in self.evidences
            ],
        }


@dataclass
class ResolutionResult:
    canonical_node_ids: dict[str, str] = field(
        default_factory=dict
    )

    decisions: list[MergeDecision] = field(
        default_factory=list
    )

    unresolved_candidates: list[
        MergeDecision
    ] = field(default_factory=list)

    def canonical_id(
        self,
        node_id: str,
    ) -> str:
        return self.canonical_node_ids.get(
            node_id,
            node_id,
        )