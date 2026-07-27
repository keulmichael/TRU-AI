from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def canonical_json(payload: dict) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def stable_id(prefix: str, payload: dict) -> str:
    return f"{prefix}-{stable_hash(canonical_json(payload))}"


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    path: str
    format: str
    title: str
    byte_size: int
    content_hash: str
    page_count: int
    extracted_page_count: int
    empty_page_numbers: tuple[int, ...] = ()
    extraction_errors: tuple[str, ...] = ()
    is_demo_source: bool = False

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "format": self.format,
            "title": self.title,
            "byte_size": self.byte_size,
            "content_hash": self.content_hash,
            "page_count": self.page_count,
            "extracted_page_count": self.extracted_page_count,
            "empty_page_numbers": list(self.empty_page_numbers),
            "extraction_errors": list(self.extraction_errors),
            "is_demo_source": self.is_demo_source,
        }


@dataclass(frozen=True)
class MemoryElement:
    element_id: str
    element_type: str
    text: str
    order: int
    position: str
    parent_id: str | None
    child_ids: tuple[str, ...]
    document_id: str
    source_id: str
    page_numbers: tuple[int, ...]
    provenance: dict
    content_hash: str
    concept_ids: tuple[str, ...] = ()
    related_element_ids: tuple[str, ...] = ()
    detection_level: str = "heuristic"
    detection_method: str = "deterministic_pattern"
    extraction_confidence: float = 0.75
    semantic_validation_status: str = "CANDIDAT"
    semantic_justification: str = "Classification heuristique non validee manuellement."
    operator_taxonomy: str | None = None

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "text": self.text,
            "order": self.order,
            "position": self.position,
            "parent_id": self.parent_id,
            "child_ids": sorted(self.child_ids),
            "document_id": self.document_id,
            "source_id": self.source_id,
            "page_numbers": sorted(self.page_numbers),
            "provenance": dict(sorted(self.provenance.items())),
            "content_hash": self.content_hash,
            "concept_ids": sorted(self.concept_ids),
            "related_element_ids": sorted(self.related_element_ids),
            "detection_level": self.detection_level,
            "detection_method": self.detection_method,
            "extraction_confidence": round(
                self.extraction_confidence,
                6,
            ),
            "semantic_validation_status": self.semantic_validation_status,
            "semantic_justification": self.semantic_justification,
            "operator_taxonomy": self.operator_taxonomy,
        }


@dataclass(frozen=True)
class CanonicalMemory:
    sources: tuple[SourceDocument, ...]
    elements: tuple[MemoryElement, ...]

    def to_dict(self) -> dict:
        return {
            "sources": [
                source.to_dict()
                for source in sorted(
                    self.sources,
                    key=lambda item: item.source_id,
                )
            ],
            "elements": [
                element.to_dict()
                for element in sorted(
                    self.elements,
                    key=lambda item: (
                        item.order,
                        item.element_id,
                    ),
                )
            ],
        }


@dataclass
class MemoryBuildReport:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_found: int = 0
    formats: dict[str, int] = field(default_factory=dict)
    total_bytes: int = 0
    announced_pages: int = 0
    extracted_pages: int = 0
    empty_pages: int = 0
    error_pages: int = 0
    extracted_characters: int = 0
    extracted_words: int = 0
    volumes_detected: int = 0
    parts_detected: int = 0
    chapters_detected: int = 0
    sections_detected: int = 0
    paragraphs_detected: int = 0
    sentences_detected: int = 0
    definitions_detected: int = 0
    axioms_detected: int = 0
    propositions_detected: int = 0
    demonstrations_detected: int = 0
    observations_detected: int = 0
    examples_detected: int = 0
    hypotheses_detected: int = 0
    operators_detected: int = 0
    concepts_detected: int = 0
    relations_detected: int = 0
    references_detected: int = 0
    unclassified_elements: int = 0
    coverage_rate: float = 0.0
    production_source_count: int = 0
    demo_source_count: int = 0
    semantic_precision_estimates: dict[str, float] = field(default_factory=dict)
    semantic_sample_counts: dict[str, int] = field(default_factory=dict)
    confirmed_elements: int = 0
    probable_elements: int = 0
    candidate_elements: int = 0
    rejected_elements: int = 0
    executable_operator_count: int = 0
    candidate_operator_count: int = 0
    non_executable_operator_count: int = 0

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "files_found": self.files_found,
            "formats": dict(sorted(self.formats.items())),
            "total_bytes": self.total_bytes,
            "announced_pages": self.announced_pages,
            "extracted_pages": self.extracted_pages,
            "empty_pages": self.empty_pages,
            "error_pages": self.error_pages,
            "extracted_characters": self.extracted_characters,
            "extracted_words": self.extracted_words,
            "volumes_detected": self.volumes_detected,
            "parts_detected": self.parts_detected,
            "chapters_detected": self.chapters_detected,
            "sections_detected": self.sections_detected,
            "paragraphs_detected": self.paragraphs_detected,
            "sentences_detected": self.sentences_detected,
            "definitions_detected": self.definitions_detected,
            "axioms_detected": self.axioms_detected,
            "propositions_detected": self.propositions_detected,
            "demonstrations_detected": self.demonstrations_detected,
            "observations_detected": self.observations_detected,
            "examples_detected": self.examples_detected,
            "hypotheses_detected": self.hypotheses_detected,
            "operators_detected": self.operators_detected,
            "concepts_detected": self.concepts_detected,
            "relations_detected": self.relations_detected,
            "references_detected": self.references_detected,
            "unclassified_elements": self.unclassified_elements,
            "coverage_rate": round(self.coverage_rate, 6),
            "production_source_count": self.production_source_count,
            "demo_source_count": self.demo_source_count,
            "semantic_precision_estimates": {
                key: round(value, 6)
                for key, value in sorted(
                    self.semantic_precision_estimates.items()
                )
            },
            "semantic_sample_counts": dict(
                sorted(self.semantic_sample_counts.items())
            ),
            "confirmed_elements": self.confirmed_elements,
            "probable_elements": self.probable_elements,
            "candidate_elements": self.candidate_elements,
            "rejected_elements": self.rejected_elements,
            "executable_operator_count": self.executable_operator_count,
            "candidate_operator_count": self.candidate_operator_count,
            "non_executable_operator_count": self.non_executable_operator_count,
        }
