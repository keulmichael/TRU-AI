from __future__ import annotations

import json
from pathlib import Path

from tru_ai.memory.builder import CanonicalMemoryBuilder
from tru_ai.memory.models import (
    CanonicalMemory,
    MemoryBuildReport,
    MemoryElement,
    SourceDocument,
)


class MemoryRepository:
    def __init__(
        self,
        sources_directory: Path,
        memory_directory: Path,
        *,
        demo_directory: Path | None = None,
    ) -> None:
        self.sources_directory = sources_directory
        self.memory_directory = memory_directory
        self.demo_directory = demo_directory

    def build(self) -> tuple[CanonicalMemory, MemoryBuildReport]:
        self.sources_directory.mkdir(parents=True, exist_ok=True)
        builder = CanonicalMemoryBuilder(
            self.sources_directory,
            demo_directory=self.demo_directory,
        )
        return builder.build()

    def write(
        self,
        memory: CanonicalMemory,
        report: MemoryBuildReport,
        manifest: dict,
    ) -> None:
        self.memory_directory.mkdir(parents=True, exist_ok=True)
        self._write_jsonl(
            self.memory_directory / "sources.jsonl",
            [source.to_dict() for source in memory.sources],
        )
        self._write_jsonl(
            self.memory_directory / "canonical_memory.jsonl",
            [element.to_dict() for element in memory.elements],
        )
        self._write_json(
            self.memory_directory / "memory_report.json",
            report.to_dict(),
        )
        self._write_json(
            self.memory_directory / "memory_manifest.json",
            manifest,
        )

    def load(self) -> CanonicalMemory:
        sources = [
            SourceDocument(**record)
            for record in self._read_jsonl(
                self.memory_directory / "sources.jsonl"
            )
        ]
        elements = []
        for record in self._read_jsonl(
            self.memory_directory / "canonical_memory.jsonl"
        ):
            elements.append(
                MemoryElement(
                    element_id=record["element_id"],
                    element_type=record["element_type"],
                    text=record["text"],
                    order=record["order"],
                    position=record["position"],
                    parent_id=record.get("parent_id"),
                    child_ids=tuple(record.get("child_ids", [])),
                    document_id=record["document_id"],
                    source_id=record["source_id"],
                    page_numbers=tuple(record.get("page_numbers", [])),
                    provenance=record.get("provenance", {}),
                    content_hash=record["content_hash"],
                    concept_ids=tuple(record.get("concept_ids", [])),
                    related_element_ids=tuple(
                        record.get("related_element_ids", [])
                    ),
                    detection_level=record.get(
                        "detection_level",
                        "heuristic",
                    ),
                    detection_method=record.get(
                        "detection_method",
                        "deterministic_pattern",
                    ),
                    extraction_confidence=record.get(
                        "extraction_confidence",
                        0.75,
                    ),
                    semantic_validation_status=record.get(
                        "semantic_validation_status",
                        "CANDIDAT",
                    ),
                    semantic_justification=record.get(
                        "semantic_justification",
                        "Classification heuristique non validee manuellement.",
                    ),
                    operator_taxonomy=record.get("operator_taxonomy"),
                )
            )
        return CanonicalMemory(
            sources=tuple(sources),
            elements=tuple(elements),
        )

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict]:
        if not path.exists():
            return []
        records = []
        with path.open("r", encoding="utf-8") as input_file:
            for line in input_file:
                if line.strip():
                    records.append(json.loads(line))
        return records

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as output_file:
            for record in sorted(
                records,
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ):
                output_file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )

    @staticmethod
    def _write_json(path: Path, record: dict) -> None:
        with path.open("w", encoding="utf-8") as output_file:
            json.dump(
                record,
                output_file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            output_file.write("\n")
