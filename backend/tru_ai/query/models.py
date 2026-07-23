from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NodeSearchResult:
    node_id: str
    label: str
    normalized_label: str
    node_type: str
    concept_id: str | None
    category: str | None
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RelationView:
    edge_id: str
    subject_id: str
    subject_label: str
    predicate: str
    object_id: str
    object_label: str
    occurrence_count: int
    confidence_average: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class NeighborView:
    node_id: str
    label: str
    normalized_label: str
    direction: str
    predicate: str
    edge_id: str
    confidence_average: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PathStep:
    edge_id: str
    subject_id: str
    subject_label: str
    predicate: str
    object_id: str
    object_label: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GraphPath:
    source_id: str
    source_label: str
    target_id: str
    target_label: str
    directed: bool
    length: int
    node_ids: tuple[str, ...]
    node_labels: tuple[str, ...]
    steps: tuple[PathStep, ...]

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_label": self.source_label,
            "target_id": self.target_id,
            "target_label": self.target_label,
            "directed": self.directed,
            "length": self.length,
            "node_ids": list(self.node_ids),
            "node_labels": list(
                self.node_labels
            ),
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
        }