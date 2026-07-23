from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Iterable


EdgeKey = tuple[str, str, str]


def canonical_edge_key(
    subject_id: str,
    predicate: str,
    object_id: str,
) -> EdgeKey:
    return (
        subject_id,
        predicate,
        object_id,
    )


def clamp_confidence(
    confidence: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )


def make_inferred_edge_id(
    subject_id: str,
    predicate: str,
    object_id: str,
) -> str:
    payload = (
        f"{subject_id}|"
        f"{predicate}|"
        f"{object_id}"
    )

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]

    return f"inferred-edge-{digest}"


def make_inference_id(
    rule_id: str,
    premise_edge_ids: Iterable[str],
    premise_edge_keys: Iterable[EdgeKey],
    subject_id: str,
    predicate: str,
    object_id: str,
    inference_depth: int,
    variable_bindings: dict[str, str],
) -> str:
    payload = {
        "inference_depth": inference_depth,
        "premise_edge_ids": sorted(
            premise_edge_ids
        ),
        "premise_edge_keys": sorted(
            list(premise_edge_keys)
        ),
        "rule_id": rule_id,
        "subject_id": subject_id,
        "predicate": predicate,
        "object_id": object_id,
        "variable_bindings": dict(
            sorted(
                variable_bindings.items()
            )
        ),
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()[:16]

    return f"inference-{digest}"


@dataclass(frozen=True)
class InferenceRule:
    rule_id: str
    name: str
    rule_type: str
    rule_family: str
    source_predicate: str
    target_predicate: str | None
    inverse_predicate: str | None
    confidence_factor: float
    enabled: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InferredEdge:
    edge_id: str
    subject_id: str
    predicate: str
    object_id: str
    rule_ids: set[str] = field(
        default_factory=set
    )
    premise_edge_ids: set[str] = field(
        default_factory=set
    )
    premise_edge_keys: set[EdgeKey] = field(
        default_factory=set
    )
    source_sentence_ids: set[str] = field(
        default_factory=set
    )
    inference_depth: int = 1
    occurrence_count: int = 0
    confidence_sum: float = 0.0
    confidence_max: float = 0.0

    @property
    def confidence_average(self) -> float:
        if self.occurrence_count == 0:
            return 0.0

        return (
            self.confidence_sum
            / self.occurrence_count
        )

    def register_evidence(
        self,
        rule_id: str,
        premise_edge_ids: Iterable[str],
        premise_edge_keys: Iterable[EdgeKey],
        source_sentence_ids: Iterable[str],
        inference_depth: int,
        confidence: float,
    ) -> None:
        confidence = clamp_confidence(
            confidence
        )

        self.rule_ids.add(rule_id)
        self.premise_edge_ids.update(
            premise_edge_ids
        )
        self.premise_edge_keys.update(
            premise_edge_keys
        )
        self.source_sentence_ids.update(
            source_sentence_ids
        )
        self.inference_depth = max(
            self.inference_depth,
            inference_depth,
        )
        self.occurrence_count += 1
        self.confidence_sum += confidence
        self.confidence_max = max(
            self.confidence_max,
            confidence,
        )

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_id": self.object_id,
            "rule_ids": sorted(
                self.rule_ids
            ),
            "premise_edge_ids": sorted(
                self.premise_edge_ids
            ),
            "premise_edge_keys": [
                list(edge_key)
                for edge_key in sorted(
                    self.premise_edge_keys
                )
            ],
            "source_sentence_ids": sorted(
                self.source_sentence_ids
            ),
            "inference_depth": (
                self.inference_depth
            ),
            "occurrence_count": (
                self.occurrence_count
            ),
            "confidence_average": round(
                self.confidence_average,
                6,
            ),
            "confidence_sum": round(
                self.confidence_sum,
                6,
            ),
            "confidence_max": round(
                self.confidence_max,
                6,
            ),
        }


@dataclass(frozen=True)
class InferenceTrace:
    inference_id: str
    inferred_edge_id: str
    rule_id: str
    premise_edge_ids: tuple[str, ...]
    premise_edge_keys: tuple[EdgeKey, ...]
    variable_bindings: dict[str, str]
    source_sentence_ids: tuple[str, ...]
    inference_depth: int
    confidence: float

    def to_dict(self) -> dict:
        return {
            "inference_id": self.inference_id,
            "inferred_edge_id": (
                self.inferred_edge_id
            ),
            "rule_id": self.rule_id,
            "premise_edge_ids": sorted(
                self.premise_edge_ids
            ),
            "premise_edge_keys": [
                list(edge_key)
                for edge_key in sorted(
                    self.premise_edge_keys
                )
            ],
            "variable_bindings": dict(
                sorted(
                    self.variable_bindings.items()
                )
            ),
            "source_sentence_ids": sorted(
                self.source_sentence_ids
            ),
            "inference_depth": (
                self.inference_depth
            ),
            "confidence": round(
                clamp_confidence(
                    self.confidence
                ),
                6,
            ),
        }


@dataclass(frozen=True)
class InferenceResult:
    inferred_edges: tuple[InferredEdge, ...]
    traces: tuple[InferenceTrace, ...]
    passes_executed: int
    max_depth_reached: int
    fixed_point_reached: bool

    def to_dict(self) -> dict:
        return {
            "inferred_edges": [
                edge.to_dict()
                for edge in self.inferred_edges
            ],
            "traces": [
                trace.to_dict()
                for trace in self.traces
            ],
            "passes_executed": (
                self.passes_executed
            ),
            "max_depth_reached": (
                self.max_depth_reached
            ),
            "fixed_point_reached": (
                self.fixed_point_reached
            ),
        }


@dataclass
class InferenceValidationReport:
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
