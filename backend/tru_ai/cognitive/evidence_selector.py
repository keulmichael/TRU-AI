from __future__ import annotations

from tru_ai.extraction.lexical_normalizer import LexicalNormalizer
from tru_ai.memory.models import CanonicalMemory, MemoryElement


PRIORITY_TYPES = {
    "Définition": 1.0,
    "Axiome": 0.92,
    "Démonstration": 0.86,
    "Proposition": 0.82,
    "Observation": 0.78,
    "Exemple": 0.7,
    "Paragraphe": 0.6,
    "Phrase": 0.45,
}
ACCEPTED_STATUSES = {"CONFIRMÉ", "PROBABLE"}


class EvidenceSelector:
    def __init__(self) -> None:
        self.normalizer = LexicalNormalizer()

    def select(
        self,
        *,
        question: str,
        concepts: tuple[str, ...],
        memory: CanonicalMemory,
        limit: int = 12,
    ) -> tuple[MemoryElement, ...]:
        if not concepts:
            return ()
        question_terms = {
            term
            for term in self.normalizer.normalize(question).split()
            if len(term) > 2
        }
        scored: list[tuple[float, MemoryElement]] = []
        seen_text_hashes: set[str] = set()
        for element in memory.elements:
            if element.element_type == "Document":
                continue
            if element.semantic_validation_status not in ACCEPTED_STATUSES:
                continue
            if element.content_hash in seen_text_hashes:
                continue
            text_terms = set(self.normalizer.normalize(element.text).split())
            concept_score = len(set(concepts) & set(element.concept_ids)) * 2.0
            lexical_score = len(question_terms & text_terms) * 0.25
            if concept_score == 0 and lexical_score == 0:
                continue
            type_score = PRIORITY_TYPES.get(element.element_type, 0.2)
            validation_score = (
                0.25
                if element.semantic_validation_status == "CONFIRMÉ"
                else 0.12
            )
            score = (
                concept_score
                + lexical_score
                + type_score
                + validation_score
                + element.extraction_confidence
            )
            if score > 0.5:
                scored.append((score, element))
                seen_text_hashes.add(element.content_hash)
        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].order,
                item[1].element_id,
            )
        )
        return tuple(element for _, element in scored[:limit])
