import json
import shutil
from pathlib import Path

from scripts.build_inferences import (
    run_pipeline,
)
from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.inference.repository import (
    InferenceRepository,
)


TEST_ROOT = (
    Path(__file__).resolve().parents[1]
    / ".pipeline_test"
)


def make_node(
    node_id: str,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=node_id,
        normalized_label=node_id,
        node_type="concept",
        aliases={node_id},
        source_sentence_ids={
            f"sentence-{node_id}"
        },
        occurrence_count=1,
    )


def make_edge(
    edge_id: str,
    subject_id: str,
    predicate: str,
    object_id: str,
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        relation_ids={f"relation-{edge_id}"},
        proposition_ids={
            f"proposition-{edge_id}"
        },
        source_sentence_ids={
            f"sentence-{edge_id}"
        },
        pattern_ids={"pattern-test"},
        extraction_methods={
            "deterministic_pattern"
        },
        occurrence_count=1,
        confidence_sum=0.9,
        confidence_max=0.9,
    )


def make_graph(
    edges: tuple[GraphEdge, ...],
) -> KnowledgeGraph:
    node_ids = sorted(
        {
            node_id
            for edge in edges
            for node_id in (
                edge.subject_id,
                edge.object_id,
            )
        }
    )

    return KnowledgeGraph(
        nodes=tuple(
            make_node(node_id)
            for node_id in node_ids
        ),
        edges=edges,
    )


def reset_directory(path: Path) -> None:
    workspace = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    resolved = path.resolve()

    if resolved.exists():
        if not str(resolved).startswith(
            str(workspace)
        ):
            raise RuntimeError(
                "Refus de supprimer un chemin "
                "hors workspace."
            )

        shutil.rmtree(resolved)

    resolved.mkdir(
        parents=True,
        exist_ok=True,
    )


def write_resolved_graph(
    root: Path,
    graph: KnowledgeGraph,
) -> None:
    repository = InferenceRepository(
        resolved_graph_directory=(
            root / "graph_resolved"
        ),
        inference_directory=(
            root / "inference"
        ),
        graph_inferred_directory=(
            root / "graph_inferred"
        ),
    )

    repository.write_jsonl(
        root
        / "graph_resolved"
        / "nodes.jsonl",
        [
            node.to_dict()
            for node in graph.nodes
        ],
    )

    repository.write_jsonl(
        root
        / "graph_resolved"
        / "edges.jsonl",
        [
            edge.to_dict()
            for edge in graph.edges
        ],
    )


def run_test_pipeline(
    root: Path,
    graph: KnowledgeGraph,
    generated_at: str = "fixed",
):
    reset_directory(root)
    write_resolved_graph(root, graph)

    source_nodes_before = (
        root
        / "graph_resolved"
        / "nodes.jsonl"
    ).read_text(encoding="utf-8")
    source_edges_before = (
        root
        / "graph_resolved"
        / "edges.jsonl"
    ).read_text(encoding="utf-8")

    manifest, valid = run_pipeline(
        source_graph_directory=(
            root / "graph_resolved"
        ),
        inference_directory=(
            root / "inference"
        ),
        graph_inferred_directory=(
            root / "graph_inferred"
        ),
        max_depth=2,
        generated_at=generated_at,
    )

    source_nodes_after = (
        root
        / "graph_resolved"
        / "nodes.jsonl"
    ).read_text(encoding="utf-8")
    source_edges_after = (
        root
        / "graph_resolved"
        / "edges.jsonl"
    ).read_text(encoding="utf-8")

    assert source_nodes_before == source_nodes_after
    assert source_edges_before == source_edges_after

    return manifest, valid


def read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def read_all_outputs(root: Path) -> dict[str, str]:
    files = {
        "inferred_edges": (
            root
            / "inference"
            / "inferred_edges.jsonl"
        ),
        "inference_traces": (
            root
            / "inference"
            / "inference_traces.jsonl"
        ),
        "inference_manifest": (
            root
            / "inference"
            / "inference_manifest.json"
        ),
        "graph_nodes": (
            root
            / "graph_inferred"
            / "nodes.jsonl"
        ),
        "graph_edges": (
            root
            / "graph_inferred"
            / "edges.jsonl"
        ),
        "adjacency": (
            root
            / "graph_inferred"
            / "adjacency.json"
        ),
        "graph_manifest": (
            root
            / "graph_inferred"
            / "inference_manifest.json"
        ),
    }

    return {
        name: path.read_text(
            encoding="utf-8"
        )
        for name, path in files.items()
    }


def normalize_generated_at(
    content: dict[str, str],
) -> dict[str, str]:
    normalized = dict(content)

    for key in (
        "inference_manifest",
        "graph_manifest",
    ):
        manifest = json.loads(
            normalized[key]
        )
        manifest["generated_at"] = (
            "<ignored>"
        )
        normalized[key] = json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

    return normalized


def test_pipeline_complete_synthetic_graph() -> None:
    root = TEST_ROOT / "complete"
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-c",
            ),
        )
    )

    manifest, valid = run_test_pipeline(
        root,
        graph,
    )

    assert valid is True
    assert manifest["version"] == "v0.8.6.0"
    assert manifest["validation"]["valid"] is True
    assert manifest["original_node_count"] == 3
    assert manifest["original_edge_count"] == 2
    assert manifest["inferred_edge_count"] == 1
    assert manifest["trace_count"] == 1
    assert manifest["enriched_edge_count"] == 3


def test_pipeline_writes_both_output_directories() -> None:
    root = TEST_ROOT / "outputs"
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            ),
        )
    )

    run_test_pipeline(root, graph)

    assert (
        root
        / "inference"
        / "inferred_edges.jsonl"
    ).exists()
    assert (
        root
        / "inference"
        / "inference_traces.jsonl"
    ).exists()
    assert (
        root
        / "inference"
        / "inference_manifest.json"
    ).exists()
    assert (
        root
        / "graph_inferred"
        / "nodes.jsonl"
    ).exists()
    assert (
        root
        / "graph_inferred"
        / "edges.jsonl"
    ).exists()
    assert (
        root
        / "graph_inferred"
        / "adjacency.json"
    ).exists()
    assert (
        root
        / "graph_inferred"
        / "inference_manifest.json"
    ).exists()


def test_pipeline_builds_graph_inferred() -> None:
    root = TEST_ROOT / "graph_inferred"
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "equivalent_to",
                "node-b",
            ),
        )
    )

    run_test_pipeline(root, graph)

    edges = (
        root
        / "graph_inferred"
        / "edges.jsonl"
    ).read_text(encoding="utf-8")

    assert "equivalent_to" in edges
    assert "deterministic_inference" in edges


def test_pipeline_accepts_no_valid_inference() -> None:
    root = TEST_ROOT / "none"
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "observe",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "observe",
                "node-c",
            ),
        )
    )

    manifest, valid = run_test_pipeline(
        root,
        graph,
    )

    assert valid is True
    assert manifest["inferred_edge_count"] == 0
    assert manifest["trace_count"] == 0
    assert manifest["enriched_edge_count"] == 2


def test_pipeline_handles_multiple_depths() -> None:
    root = TEST_ROOT / "depths"
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-c",
            ),
            make_edge(
                "edge-3",
                "node-c",
                "is_a",
                "node-d",
            ),
        )
    )

    manifest, valid = run_test_pipeline(
        root,
        graph,
    )

    assert valid is True
    assert manifest["max_depth_reached"] == 2
    assert manifest["inferred_edge_count"] == 3


def test_pipeline_reaches_fixed_point() -> None:
    root = TEST_ROOT / "fixed_point"
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            ),
        )
    )

    manifest, valid = run_test_pipeline(
        root,
        graph,
    )

    assert valid is True
    assert manifest["fixed_point_reached"] is True


def test_pipeline_two_runs_are_identical_except_generated_at() -> None:
    graph = make_graph(
        (
            make_edge(
                "edge-1",
                "node-a",
                "is_a",
                "node-b",
            ),
            make_edge(
                "edge-2",
                "node-b",
                "is_a",
                "node-c",
            ),
        )
    )

    root = TEST_ROOT / "repeat"

    run_test_pipeline(
        root,
        graph,
        generated_at="first-time",
    )
    first_outputs = read_all_outputs(root)

    run_test_pipeline(
        root,
        graph,
        generated_at="second-time",
    )
    second_outputs = read_all_outputs(root)

    assert normalize_generated_at(
        first_outputs
    ) == normalize_generated_at(
        second_outputs
    )


def teardown_module() -> None:
    if TEST_ROOT.exists():
        reset_directory(TEST_ROOT)
        TEST_ROOT.rmdir()
