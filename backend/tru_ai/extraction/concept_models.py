from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConceptDefinition:
    concept_id: str
    preferred_label: str
    category: str
    aliases: tuple[str, ...]
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ConceptOccurrence:
    occurrence_id: str
    sentence_id: str
    concept_id: str
    preferred_label: str
    category: str
    matched_text: str
    matched_alias: str
    start_char: int
    end_char: int
    confidence: float
    extraction_method: str = "deterministic_lexicon"

    def to_dict(self) -> dict:
        return asdict(self)