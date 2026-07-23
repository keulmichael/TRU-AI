from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class GraphNode:
    node_id: str
    label: str
    normalized_label: str
    node_type: str
    concept_id: str | None = None
    category: str | None = None
    aliases: set[str] = field(default_factory=set)
    source_sentence_ids: set[str] = field(
        default_factory=set
    )
    occurrence_count: int = 0

    def register_occurrence(
        self,
        label: str,
        sentence_id: str,
    ) -> None:
        if label:
            self.aliases.add(label)

        if sentence_id:
            self.source_sentence_ids.add(
                sentence_id
            )

        self.occurrence_count += 1

    def to_dict(self) -> dict:
        record = asdict(self)

        record["aliases"] = sorted(
            self.aliases
        )

        record["source_sentence_ids"] = sorted(
            self.source_sentence_ids
        )

        return record


@dataclass
class GraphEdge:
    edge_id: str
    subject_id: str
    predicate: str
    object_id: str
    relation_ids: set[str] = field(
        default_factory=set
    )
    proposition_ids: set[str] = field(
        default_factory=set
    )
    source_sentence_ids: set[str] = field(
        default_factory=set
    )
    pattern_ids: set[str] = field(
        default_factory=set
    )
    extraction_methods: set[str] = field(
        default_factory=set
    )
    occurrence_count: int = 0
    confidence_sum: float = 0.0
    confidence_max: float = 0.0

    def register_relation(
        self,
        relation_id: str,
        proposition_id: str,
        sentence_id: str,
        pattern_id: str,
        extraction_method: str,
        confidence: float,
    ) -> None:
        self.relation_ids.add(relation_id)
        self.proposition_ids.add(
            proposition_id
        )
        self.source_sentence_ids.add(
            sentence_id
        )
        self.pattern_ids.add(pattern_id)
        self.extraction_methods.add(
            extraction_method
        )

        self.occurrence_count += 1
        self.confidence_sum += confidence
        self.confidence_max = max(
            self.confidence_max,
            confidence,
        )

    @property
    def confidence_average(self) -> float:
        if self.occurrence_count == 0:
            return 0.0

        return (
            self.confidence_sum
            / self.occurrence_count
        )

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_id": self.object_id,
            "relation_ids": sorted(
                self.relation_ids
            ),
            "proposition_ids": sorted(
                self.proposition_ids
            ),
            "source_sentence_ids": sorted(
                self.source_sentence_ids
            ),
            "pattern_ids": sorted(
                self.pattern_ids
            ),
            "extraction_methods": sorted(
                self.extraction_methods
            ),
            "occurrence_count": (
                self.occurrence_count
            ),
            "confidence_average": round(
                self.confidence_average,
                6,
            ),
            "confidence_max": round(
                self.confidence_max,
                6,
            ),
        }


@dataclass(frozen=True)
class GraphValidationIssue:
    issue_type: str
    severity: str
    message: str
    resource_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GraphValidationReport:
    valid: bool
    node_count: int
    edge_count: int
    isolated_node_count: int
    self_loop_count: int
    duplicate_edge_count: int
    dangling_edge_count: int
    issues: tuple[
        GraphValidationIssue,
        ...,
    ]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "isolated_node_count": (
                self.isolated_node_count
            ),
            "self_loop_count": (
                self.self_loop_count
            ),
            "duplicate_edge_count": (
                self.duplicate_edge_count
            ),
            "dangling_edge_count": (
                self.dangling_edge_count
            ),
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
        }