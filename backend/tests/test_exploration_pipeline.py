import json
import shutil
from pathlib import Path

from scripts import build_exploration_indexes


def normalize_manifest(text: str) -> str:
    manifest = json.loads(text)
    manifest["generated_at"] = "<ignored>"
    return json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def test_pipeline_real_outputs_and_manifest(monkeypatch, tmp_path) -> None:
    output = tmp_path / "exploration"
    monkeypatch.setattr(
        build_exploration_indexes,
        "EXPLORATION_DIRECTORY",
        output,
    )
    manifest, valid = build_exploration_indexes.run_pipeline(
        generated_at="fixed"
    )

    assert valid is True
    assert manifest["version"] == "v0.8.8.0"
    assert manifest["validation"]["valid"] is True
    assert (output / "node_index.json").exists()
    assert (output / "exploration_manifest.json").exists()


def test_pipeline_two_builds_identical_except_generated_at(monkeypatch, tmp_path) -> None:
    output = tmp_path / "exploration"
    monkeypatch.setattr(
        build_exploration_indexes,
        "EXPLORATION_DIRECTORY",
        output,
    )
    build_exploration_indexes.run_pipeline(generated_at="first")
    first = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(output.iterdir())
    }
    shutil.rmtree(output)
    build_exploration_indexes.run_pipeline(generated_at="second")
    second = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(output.iterdir())
    }
    first["exploration_manifest.json"] = normalize_manifest(
        first["exploration_manifest.json"]
    )
    second["exploration_manifest.json"] = normalize_manifest(
        second["exploration_manifest.json"]
    )
    assert first == second


def test_pipeline_does_not_modify_sources(monkeypatch, tmp_path) -> None:
    graph_edges = Path(
        "C:/Sites/Projects/TRU-AI/corpus/graph_inferred/edges.jsonl"
    )
    reasoning = Path(
        "C:/Sites/Projects/TRU-AI/corpus/reasoning/explanations.jsonl"
    )
    before = (
        graph_edges.read_text(encoding="utf-8"),
        reasoning.read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(
        build_exploration_indexes,
        "EXPLORATION_DIRECTORY",
        tmp_path / "exploration",
    )
    build_exploration_indexes.run_pipeline(generated_at="fixed")
    after = (
        graph_edges.read_text(encoding="utf-8"),
        reasoning.read_text(encoding="utf-8"),
    )
    assert before == after
