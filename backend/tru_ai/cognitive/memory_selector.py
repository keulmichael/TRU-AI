from __future__ import annotations

from tru_ai.cognitive.evidence_selector import EvidenceSelector
from tru_ai.memory.models import CanonicalMemory, MemoryElement


class MemorySelector:
    def __init__(self) -> None:
        self.evidence_selector = EvidenceSelector()

    def select_passages(
        self,
        *,
        question: str,
        concepts: tuple[str, ...],
        memory: CanonicalMemory,
    ) -> tuple[MemoryElement, ...]:
        return self.evidence_selector.select(
            question=question,
            concepts=concepts,
            memory=memory,
        )
