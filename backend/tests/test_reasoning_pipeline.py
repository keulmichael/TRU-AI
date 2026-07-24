import json
import shutil
from pathlib import Path

from scripts.build_explanations import (
    run_pipeline,
)
from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.inference.engine import InferenceEngine
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.inference.validator import (
    InferenceValidator,
)


TEST_ROOT = (
    Path(__file__).resolve().parents[1]
    / ".reasoning_pipeline"
)


def make_node(node_id: str) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=node_id,
        normalized_label=node_id,
        node_type="concept",
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
        source_sentence_ids={
            f"sentence-{edge_id}"
        },
        occurrence_count=1,
        confidence_sum=0.9,
        confidence_max=0.9,
    )


def reset_directory(path: Path) -> None:
    workspace = Path(__file__).resolve().parents[2]
    if path.exists():
        resolved = path.resolve()
        if not str(resolved).startswith(
            str(workspace)
        ):
            raise RuntimeError(
                "Unsafe test path"
            )
        shutil.rmtree(resolved)
    path.mkdir(parents=True, exist_ok=True)


def make_graph(edges) -> KnowledgeGraph:
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
        edges=tuple(edges),
    )


def prepare_inputs(root: Path, graph: KnowledgeGraph):
    inference = InferenceEngine().run(graph)
    validation = InferenceValidator().validate(
        graph,
        inference,
    )
    writer = InferenceRepository(
        root / "graph_resolved",
        root / "inference",
        root / "graph_inferred",
    )
    writer.write_outputs(
        graph,
        inference,
        validation,
        {"version": "test"},
    )
    return inference


def run_test_pipeline(root: Path, graph: KnowledgeGraph, generated_at: str):
    reset_directory(root)
    inference = prepare_inputs(root, graph)
    graph_before = (
        root
        / "graph_inferred"
        / "edges.jsonl"
    ).read_text(encoding="utf-8")
    inference_before = (
        root
        / "inference"
        / "inference_traces.jsonl"
    ).read_text(encoding="utf-8")

    manifest, valid = run_pipeline(
        graph_inferred_directory=(
            root / "graph_inferred"
        ),
        inference_directory=(
            root / "inference"
        ),
        reasoning_directory=(
            root / "reasoning"
        ),
        generated_at=generated_at,
    )

    assert graph_before == (
        root
        / "graph_inferred"
        / "edges.jsonl"
    ).read_text(encoding="utf-8")
    assert inference_before == (
        root
        / "inference"
        / "inference_traces.jsonl"
    ).read_text(encoding="utf-8")

    return inference, manifest, valid


def read_outputs(root: Path) -> dict[str, str]:
    paths = {
        "explanations": (
            root
            / "reasoning"
            / "explanations.jsonl"
        ),
        "proof_trees": (
            root
            / "reasoning"
            / "proof_trees.jsonl"
        ),
        "manifest": (
            root
            / "reasoning"
            / "reasoning_manifest.json"
        ),
    }
    return {
        name: path.read_text(
            encoding="utf-8"
        )
        for name, path in paths.items()
    }


def normalize_manifest(outputs: dict[str, str]):
    normalized = dict(outputs)
    manifest = json.loads(
        normalized["manifest"]
    )
    manifest["generated_at"] = "<ignored>"
    normalized["manifest"] = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    return normalized


def test_reasoning_pipeline_manifest_valid() -> None:
    root = TEST_ROOT / "valid"
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "contains",
                "node-b",
            )
        ]
    )
    inference, manifest, valid = run_test_pipeline(
        root,
        graph,
        "fixed",
    )

    assert valid is True
    assert manifest["version"] == "v0.8.7.0"
    assert manifest["validation"]["valid"] is True
    assert manifest["inferred_edge_count"] == len(
        inference.inferred_edges
    )
    assert manifest["explanation_count"] == 1
    assert manifest["proof_tree_count"] == 1


def test_reasoning_pipeline_accepts_empty_inference() -> None:
    root = TEST_ROOT / "empty"
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "observe",
                "node-b",
            )
        ]
    )
    _, manifest, valid = run_test_pipeline(
        root,
        graph,
        "fixed",
    )

    assert valid is True
    assert manifest["inferred_edge_count"] == 0
    assert manifest["explanation_count"] == 0
    assert manifest["proof_tree_count"] == 0
    assert manifest["maximum_proof_depth"] == 0


def test_reasoning_pipeline_two_builds_match_except_generated_at() -> None:
    root = TEST_ROOT / "repeat"
    graph = make_graph(
        [
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
        ]
    )
    run_test_pipeline(
        root,
        graph,
        "first",
    )
    first = read_outputs(root)
    run_test_pipeline(
        root,
        graph,
        "second",
    )
    second = read_outputs(root)

    assert normalize_manifest(first) == normalize_manifest(
        second
    )


def test_reasoning_pipeline_writes_outputs() -> None:
    root = TEST_ROOT / "outputs"
    graph = make_graph(
        [
            make_edge(
                "edge-1",
                "node-a",
                "equivalent_to",
                "node-b",
            )
        ]
    )
    run_test_pipeline(root, graph, "fixed")

    assert (
        root
        / "reasoning"
        / "explanations.jsonl"
    ).exists()
    assert (
        root
        / "reasoning"
        / "proof_trees.jsonl"
    ).exists()
    assert (
        root
        / "reasoning"
        / "reasoning_manifest.json"
    ).exists()


def teardown_module() -> None:
    if TEST_ROOT.exists():
        reset_directory(TEST_ROOT)
        TEST_ROOT.rmdir()
