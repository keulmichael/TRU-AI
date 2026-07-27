from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable


EdgeKey = tuple[str, str, str]


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


def make_path_id(
    start_node_id: str,
    end_node_id: str,
    edge_ids: Iterable[str],
) -> str:
    return deterministic_id(
        "graph-path",
        {
            "end_node_id": end_node_id,
            "edge_ids": tuple(edge_ids),
            "start_node_id": start_node_id,
        },
    )


def make_pattern_match_id(
    bindings: dict[str, str],
    edge_ids: Iterable[str],
) -> str:
    return deterministic_id(
        "pattern-match",
        {
            "bindings": dict(
                sorted(bindings.items())
            ),
            "edge_ids": sorted(edge_ids),
        },
    )


@dataclass(frozen=True)
class GraphQuery:
    start_node_id: str | None = None
    end_node_id: str | None = None
    predicates: tuple[str, ...] = ()
    direction: str = "both"
    maximum_depth: int = 2
    include_source_edges: bool = True
    include_inferred_edges: bool = True
    minimum_confidence: float = 0.0
    limit: int = 50

    def to_dict(self) -> dict:
        return {
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "predicates": sorted(
                self.predicates
            ),
            "direction": self.direction,
            "maximum_depth": self.maximum_depth,
            "include_source_edges": (
                self.include_source_edges
            ),
            "include_inferred_edges": (
                self.include_inferred_edges
            ),
            "minimum_confidence": round(
                self.minimum_confidence,
                6,
            ),
            "limit": self.limit,
        }


@dataclass(frozen=True)
class GraphPathStep:
    position: int
    edge_id: str
    subject_id: str
    predicate: str
    object_id: str
    direction: str
    inferred: bool
    confidence: float
    explanation_id: str | None

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "confidence": round(
                self.confidence,
                6,
            ),
        }


@dataclass(frozen=True)
class GraphPath:
    path_id: str
    start_node_id: str
    end_node_id: str
    steps: tuple[GraphPathStep, ...]
    length: int
    minimum_confidence: float
    inferred_edge_count: int

    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
            "length": self.length,
            "minimum_confidence": round(
                self.minimum_confidence,
                6,
            ),
            "inferred_edge_count": (
                self.inferred_edge_count
            ),
        }


@dataclass(frozen=True)
class NeighborhoodResult:
    center_node_id: str
    depth: int
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    paths: tuple[GraphPath, ...]
    truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "center_node_id": self.center_node_id,
            "depth": self.depth,
            "node_ids": sorted(self.node_ids),
            "edge_ids": sorted(self.edge_ids),
            "paths": [
                path.to_dict()
                for path in self.paths
            ],
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class PatternConstraint:
    subject: str
    predicate: str | None
    object: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GraphPattern:
    variables: tuple[str, ...]
    constraints: tuple[PatternConstraint, ...]
    maximum_results: int = 100

    def to_dict(self) -> dict:
        return {
            "variables": sorted(self.variables),
            "constraints": [
                constraint.to_dict()
                for constraint
                in self.constraints
            ],
            "maximum_results": (
                self.maximum_results
            ),
        }


@dataclass(frozen=True)
class PatternMatch:
    match_id: str
    bindings: dict[str, str]
    edge_ids: tuple[str, ...]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "bindings": dict(
                sorted(
                    self.bindings.items()
                )
            ),
            "edge_ids": sorted(self.edge_ids),
            "confidence": round(
                self.confidence,
                6,
            ),
        }


@dataclass(frozen=True)
class ExplorationResult:
    nodes: tuple[dict, ...]
    edges: tuple[dict, ...]
    paths: tuple[GraphPath, ...]
    explanations: tuple[dict, ...]
    truncated: bool

    def to_dict(self) -> dict:
        return {
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "paths": [
                path.to_dict()
                for path in self.paths
            ],
            "explanations": list(
                self.explanations
            ),
            "truncated": self.truncated,
        }
