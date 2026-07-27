from __future__ import annotations

from tru_ai.extraction.concept_lexicon import ConceptLexicon
from tru_ai.extraction.lexical_normalizer import LexicalNormalizer
from tru_ai.memory.models import CanonicalMemory


class ConceptSelector:
    def __init__(self, lexicon: ConceptLexicon | None = None) -> None:
        self.lexicon = lexicon or ConceptLexicon()
        self.normalizer = LexicalNormalizer()

    def detect(self, question: str, memory: CanonicalMemory) -> tuple[str, ...]:
        normalized = self.normalizer.normalize(question)
        concept_ids: set[str] = set()
        for alias, concept in self.lexicon.aliases_by_length():
            if alias and alias in normalized:
                concept_ids.add(concept.concept_id)
        if "delta" in normalized:
            concept_ids.add("delta")
        if "burn out" in normalized or "burnout" in normalized:
            concept_ids.add("burn_out")
            concept_ids.update(
                {
                    "delta",
                    "observation",
                    "reconnaissance",
                    "transformation",
                    "tru",
                }
            )
        return tuple(sorted(concept_ids))
