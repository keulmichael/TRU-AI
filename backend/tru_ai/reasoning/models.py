from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Iterable

from tru_ai.inference.models import EdgeKey


def canonical_payload(
    payload: dict,
) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def make_reasoning_step_id(
    edge_id: str,
    role: str,
    depth: int,
) -> str:
    payload = canonical_payload(
        {
            "depth": depth,
            "edge_id": edge_id,
            "role": role,
        }
    )
    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]
    return f"reasoning-step-{digest}"


def make_proof_node_id(
    edge_id: str,
    edge_key: EdgeKey,
    node_type: str,
    rule_id: str | None,
    depth: int,
    child_node_ids: Iterable[str],
    *,
    root: bool = False,
) -> str:
    payload = canonical_payload(
        {
            "child_node_ids": sorted(
                child_node_ids
            ),
            "depth": depth,
            "edge_id": edge_id,
            "edge_key": edge_key,
            "node_type": node_type,
            "rule_id": rule_id,
        }
    )
    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]
    prefix = "proof-tree" if root else "proof-node"
    return f"{prefix}-{digest}"


def make_explanation_id(
    inferred_edge_id: str,
    conclusion_edge_key: EdgeKey,
    proof_tree_id: str,
    rule_ids: Iterable[str],
) -> str:
    payload = canonical_payload(
        {
            "conclusion_edge_key": conclusion_edge_key,
            "inferred_edge_id": inferred_edge_id,
            "proof_tree_id": proof_tree_id,
            "rule_ids": sorted(rule_ids),
        }
    )
    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]
    return f"explanation-{digest}"


@dataclass(frozen=True)
class ReasoningStep:
    step_id: str
    step_number: int
    edge_id: str
    edge_key: EdgeKey
    role: str
    depth: int
    confidence: float
    source_sentence_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "edge_id": self.edge_id,
            "edge_key": list(self.edge_key),
            "role": self.role,
            "depth": self.depth,
            "confidence": round(
                self.confidence,
                6,
            ),
            "source_sentence_ids": sorted(
                self.source_sentence_ids
            ),
        }


@dataclass(frozen=True)
class ProofTreeNode:
    node_id: str
    edge_id: str
    edge_key: EdgeKey
    node_type: str
    rule_id: str | None
    confidence: float
    depth: int
    children: tuple[ProofTreeNode, ...] = ()

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "edge_id": self.edge_id,
            "edge_key": list(self.edge_key),
            "node_type": self.node_type,
            "rule_id": self.rule_id,
            "confidence": round(
                self.confidence,
                6,
            ),
            "depth": self.depth,
            "children": [
                child.to_dict()
                for child in self.children
            ],
        }


@dataclass(frozen=True)
class ReasoningExplanation:
    explanation_id: str
    inferred_edge_id: str
    conclusion_edge_key: EdgeKey
    rule_ids: tuple[str, ...]
    steps: tuple[ReasoningStep, ...]
    proof_tree_id: str
    maximum_depth: int
    confidence: float
    deterministic_text: str

    def to_dict(self) -> dict:
        return {
            "explanation_id": self.explanation_id,
            "inferred_edge_id": self.inferred_edge_id,
            "conclusion_edge_key": list(
                self.conclusion_edge_key
            ),
            "rule_ids": sorted(self.rule_ids),
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
            "proof_tree_id": self.proof_tree_id,
            "maximum_depth": self.maximum_depth,
            "confidence": round(
                self.confidence,
                6,
            ),
            "deterministic_text": (
                self.deterministic_text
            ),
        }


@dataclass(frozen=True)
class ReasoningResult:
    explanations: tuple[ReasoningExplanation, ...]
    proof_trees: tuple[ProofTreeNode, ...]
    explained_edge_count: int
    unexplained_edge_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "explanations": [
                explanation.to_dict()
                for explanation in self.explanations
            ],
            "proof_trees": [
                proof_tree.to_dict()
                for proof_tree in self.proof_trees
            ],
            "explained_edge_count": (
                self.explained_edge_count
            ),
            "unexplained_edge_ids": sorted(
                self.unexplained_edge_ids
            ),
        }


@dataclass
class ReasoningValidationReport:
    valid: bool = True
    errors: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def add_error(
        self,
        message: str,
    ) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }
