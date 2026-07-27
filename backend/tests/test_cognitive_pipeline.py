from __future__ import annotations

import json

from scripts.build_cognitive_memory import run_pipeline
from tru_ai.memory.repository import MemoryRepository


def test_cognitive_memory_pipeline_with_real_absent_sources(tmp_path, monkeypatch):
    sources = tmp_path / "sources"
    demo = tmp_path / "raw"
    memory = tmp_path / "memory"
    demo.mkdir()
    (demo / "demo.md").write_text("# Demo\n\nDelta est défini comme un écart.", encoding="utf-8")

    monkeypatch.setattr("scripts.build_cognitive_memory.SOURCES_DIRECTORY", sources)
    monkeypatch.setattr("scripts.build_cognitive_memory.DEMO_DIRECTORY", demo)
    monkeypatch.setattr("scripts.build_cognitive_memory.MEMORY_DIRECTORY", memory)

    manifest, valid = run_pipeline(generated_at="fixed")

    assert valid is True
    assert manifest["memory"]["production_source_count"] == 0
    assert manifest["memory"]["demo_source_count"] == 1
    assert manifest["validation"]["warnings"]
    assert (memory / "canonical_memory.jsonl").exists()


def test_cognitive_memory_pipeline_is_deterministic(tmp_path, monkeypatch):
    sources = tmp_path / "sources"
    memory = tmp_path / "memory"
    sources.mkdir()
    (sources / "traite.md").write_text(
        "# Delta\n\nDelta est défini comme un écart.",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.build_cognitive_memory.SOURCES_DIRECTORY", sources)
    monkeypatch.setattr("scripts.build_cognitive_memory.DEMO_DIRECTORY", tmp_path / "raw")
    monkeypatch.setattr("scripts.build_cognitive_memory.MEMORY_DIRECTORY", memory)

    first, _ = run_pipeline(generated_at="fixed")
    first_files = {
        path.name: path.read_text(encoding="utf-8")
        for path in memory.iterdir()
    }
    second, _ = run_pipeline(generated_at="fixed")
    second_files = {
        path.name: path.read_text(encoding="utf-8")
        for path in memory.iterdir()
    }

    assert first == second
    assert first_files == second_files
    assert json.loads((memory / "memory_report.json").read_text(encoding="utf-8"))["valid"]


def test_repository_reports_missing_real_treatise_without_inventing_content(tmp_path):
    sources = tmp_path / "sources"
    demo = tmp_path / "raw"
    demo.mkdir()
    (demo / "demo.md").write_text("# Demo\n\nTexte bref.", encoding="utf-8")

    _, report = MemoryRepository(
        sources,
        tmp_path / "memory",
        demo_directory=demo,
    ).build()

    assert report.production_source_count == 0
    assert report.demo_source_count == 1
    assert report.warnings
