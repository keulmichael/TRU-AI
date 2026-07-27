from tests.test_exploration_indexes import make_graph
from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.exploration.repository import ExplorationRepository
from tru_ai.exploration.validator import ExplorationValidator


def test_repository_writes_index_files(tmp_path) -> None:
    indexes = ExplorationIndexes(make_graph())
    repository = ExplorationRepository(
        tmp_path / "graph_inferred",
        tmp_path / "reasoning",
        tmp_path / "exploration",
    )
    report = ExplorationValidator().validate_indexes(indexes)
    repository.write_indexes(
        indexes,
        {
            "version": "v0.8.8.0",
            "validation": report.to_dict(),
        },
    )

    assert (tmp_path / "exploration" / "node_index.json").exists()
    assert (tmp_path / "exploration" / "predicate_index.json").exists()
    assert (tmp_path / "exploration" / "outgoing_index.json").exists()
    assert (tmp_path / "exploration" / "incoming_index.json").exists()
    assert (
        tmp_path
        / "exploration"
        / "edge_explanation_index.json"
    ).exists()
    assert (
        tmp_path / "exploration" / "exploration_manifest.json"
    ).exists()


def test_repository_writes_deterministically(tmp_path) -> None:
    indexes = ExplorationIndexes(make_graph())
    repository = ExplorationRepository(
        tmp_path / "graph_inferred",
        tmp_path / "reasoning",
        tmp_path / "exploration",
    )
    manifest = {"version": "v0.8.8.0"}
    repository.write_indexes(indexes, manifest)
    first = (
        tmp_path / "exploration" / "outgoing_index.json"
    ).read_text(encoding="utf-8")
    repository.write_indexes(indexes, manifest)
    second = (
        tmp_path / "exploration" / "outgoing_index.json"
    ).read_text(encoding="utf-8")

    assert first == second
