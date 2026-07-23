from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Proposition:
    proposition_id: str
    sentence_id: str
    document_id: str
    section_id: str
    paragraph_id: str
    subject_text: str
    predicate_text: str
    object_text: str
    subject_normalized: str
    predicate_normalized: str
    object_normalized: str
    start_char: int
    end_char: int
    confidence: float
    extraction_method: str
    pattern_id: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Relation:
    relation_id: str
    proposition_id: str
    sentence_id: str
    subject_id: str
    subject_label: str
    predicate: str
    object_id: str
    object_label: str
    confidence: float
    extraction_method: str
    pattern_id: str

    def to_dict(self) -> dict:
        return asdict(self)