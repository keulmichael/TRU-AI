from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from tru_ai.memory.repository import MemoryRepository


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DIRECTORY = PROJECT_ROOT / "corpus" / "sources"
DEMO_DIRECTORY = PROJECT_ROOT / "corpus" / "raw"
MEMORY_DIRECTORY = PROJECT_ROOT / "corpus" / "memory"
VERSION = "v0.9.1"


def build_manifest(
    *,
    generated_at: str,
    report,
) -> dict:
    return {
        "version": VERSION,
        "generated_at": generated_at,
        "source_paths": {
            "sources_directory": str(SOURCES_DIRECTORY),
            "demo_directory": str(DEMO_DIRECTORY),
        },
        "output_paths": {
            "sources": str(MEMORY_DIRECTORY / "sources.jsonl"),
            "canonical_memory": str(
                MEMORY_DIRECTORY / "canonical_memory.jsonl"
            ),
            "memory_report": str(MEMORY_DIRECTORY / "memory_report.json"),
            "memory_manifest": str(
                MEMORY_DIRECTORY / "memory_manifest.json"
            ),
        },
        "memory": report.to_dict(),
        "validation": {
            "valid": report.valid,
            "errors": list(report.errors),
            "warnings": list(report.warnings),
        },
    }


def run_pipeline(generated_at: str | None = None) -> tuple[dict, bool]:
    repository = MemoryRepository(
        sources_directory=SOURCES_DIRECTORY,
        memory_directory=MEMORY_DIRECTORY,
        demo_directory=DEMO_DIRECTORY,
    )
    memory, report = repository.build()
    manifest = build_manifest(
        generated_at=generated_at or datetime.now(UTC).isoformat(),
        report=report,
    )
    repository.write(memory, report, manifest)
    print()
    print("TRU-AI — Cognitive Memory Builder")
    print("--------------------------------")
    print(f"Sources found              : {report.files_found}")
    print(f"Production sources         : {report.production_source_count}")
    print(f"Demo sources               : {report.demo_source_count}")
    print(f"Formats                    : {json.dumps(report.formats, ensure_ascii=False, sort_keys=True)}")
    print(f"Pages announced            : {report.announced_pages}")
    print(f"Pages extracted            : {report.extracted_pages}")
    print(f"Empty pages                : {report.empty_pages}")
    print(f"Characters extracted       : {report.extracted_characters}")
    print(f"Words extracted            : {report.extracted_words}")
    print(f"Definitions detected       : {report.definitions_detected}")
    print(f"Axioms detected            : {report.axioms_detected}")
    print(f"Propositions detected      : {report.propositions_detected}")
    print(f"Demonstrations detected    : {report.demonstrations_detected}")
    print(f"Observations detected      : {report.observations_detected}")
    print(f"Examples detected          : {report.examples_detected}")
    print(f"Hypotheses detected        : {report.hypotheses_detected}")
    print(f"Operators detected         : {report.operators_detected}")
    print(f"Executable operators       : {report.executable_operator_count}")
    print(f"Candidate operators        : {report.candidate_operator_count}")
    print(f"Non-executable operators   : {report.non_executable_operator_count}")
    print(f"Concept links detected     : {report.concepts_detected}")
    print(f"Volumes detected           : {report.volumes_detected}")
    print(f"Parts detected             : {report.parts_detected}")
    print(f"Chapters detected          : {report.chapters_detected}")
    print(f"Sections detected          : {report.sections_detected}")
    print(f"Paragraphs detected        : {report.paragraphs_detected}")
    print(f"Sentences detected         : {report.sentences_detected}")
    print(f"References detected        : {report.references_detected}")
    print(f"Unclassified elements      : {report.unclassified_elements}")
    print(f"Coverage rate              : {report.coverage_rate:.6f}")
    print(f"Confirmed elements         : {report.confirmed_elements}")
    print(f"Probable elements          : {report.probable_elements}")
    print(f"Candidate elements         : {report.candidate_elements}")
    print(f"Rejected elements          : {report.rejected_elements}")
    print(f"Semantic precision         : {json.dumps(report.semantic_precision_estimates, ensure_ascii=False, sort_keys=True)}")
    print(f"Validation                 : {report.valid}")
    if report.errors:
        print("Errors:")
        for error in report.errors:
            print(f"- {error}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"- {warning}")
    return manifest, report.valid


def main() -> None:
    _, valid = run_pipeline()
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
