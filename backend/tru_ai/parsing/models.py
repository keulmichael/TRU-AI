from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ParsedSection:
    section_id: str
    document_id: str
    position: int
    level: int
    title: str
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ParsedParagraph:
    paragraph_id: str
    document_id: str
    section_id: str
    position: int
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ParsedSentence:
    sentence_id: str
    document_id: str
    section_id: str
    paragraph_id: str
    position: int
    content: str
    word_count: int

    def to_dict(self) -> dict:
        return asdict(self)