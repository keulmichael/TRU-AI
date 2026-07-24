import json

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.inference.engine import InferenceEngine
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.reasoning.repository import (
    ReasoningRepository,
)
from tru_ai.reasoning.validator import (
    ReasoningValidator,
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


def make_graph(predicate: str = "contains"):
    return KnowledgeGraph(
        nodes=(
            make_node("node-a"),
            make_node("node-b"),
        ),
        edges=(
            make_edge(
                "edge-1",
                "node-a",
                predicate,
                "node-b",
            ),
        ),
    )


def prepare_corpus(root, graph):
    inference = InferenceEngine().run(graph)
    enriched = (
        InferenceRepository.build_enriched_graph(
            graph,
            inference.inferred_edges,
        )
    )
    writer = InferenceRepository(
        root / "graph_resolved",
        root / "inference",
        root / "graph_inferred",
    )
    writer.write_outputs(
        graph,
        inference,
        validation=ReasoningValidator()
        .compare_results(
            NoneResult(),
            NoneResult(),
        ),
        manifest={"version": "test"},
    )
    writer.write_jsonl(
        root / "graph_inferred" / "nodes.jsonl",
        [
            node.to_dict()
            for node in enriched.nodes
        ],
    )
    writer.write_jsonl(
        root / "graph_inferred" / "edges.jsonl",
        [
            edge.to_dict()
            for edge in enriched.edges
        ],
    )
    return inference, enriched


class NoneResult:
    def to_dict(self):
        return {}


def make_repository(root) -> ReasoningRepository:
    return ReasoningRepository(
        graph_inferred_directory=(
            root / "graph_inferred"
        ),
        inference_directory=(
            root / "inference"
        ),
        reasoning_directory=(
            root / "reasoning"
        ),
    )


def test_repository_builds_and_writes_result(tmp_path) -> None:
    inference, enriched = prepare_corpus(
        tmp_path,
        make_graph(),
    )
    repository = make_repository(tmp_path)

    result = repository.build_result()
    validation = ReasoningValidator().validate(
        enriched,
        inference.inferred_edges,
        inference.traces,
        result,
    )
    repository.write_result(
        result,
        validation,
        manifest={
            "version": "v0.8.7.0",
            "generated_at": "fixed",
        },
    )

    assert (
        tmp_path
        / "reasoning"
        / "explanations.jsonl"
    ).exists()
    assert (
        tmp_path
        / "reasoning"
        / "proof_trees.jsonl"
    ).exists()
    assert (
        tmp_path
        / "reasoning"
        / "reasoning_manifest.json"
    ).exists()
    assert validation.valid is True


def test_repository_reads_jsonl_and_round_trips(tmp_path) -> None:
    inference, _ = prepare_corpus(
        tmp_path,
        make_graph(),
    )
    repository = make_repository(tmp_path)
    result = repository.build_result()
    repository.write_result(
        result,
        ReasoningValidator.compare_results(
            result,
            result,
        ),
        manifest={"version": "test"},
    )

    loaded = repository.load_reasoning_result()

    assert loaded.to_dict() == result.to_dict()
    assert len(inference.inferred_edges) == 1


def test_repository_accepts_empty_inference(tmp_path) -> None:
    inference, enriched = prepare_corpus(
        tmp_path,
        make_graph("observe"),
    )
    result = make_repository(
        tmp_path
    ).build_result()

    report = ReasoningValidator().validate(
        enriched,
        inference.inferred_edges,
        inference.traces,
        result,
    )

    assert result.explanations == ()
    assert result.proof_trees == ()
    assert report.valid is True


def test_repository_serialization_is_deterministic(tmp_path) -> None:
    inference, enriched = prepare_corpus(
        tmp_path,
        make_graph(),
    )
    repository = make_repository(tmp_path)
    result = repository.build_result()
    validation = ReasoningValidator().validate(
        enriched,
        inference.inferred_edges,
        inference.traces,
        result,
    )
    repository.write_result(
        result,
        validation,
        {"version": "test"},
    )
    first = (
        tmp_path
        / "reasoning"
        / "explanations.jsonl"
    ).read_text(encoding="utf-8")

    repository.write_result(
        result,
        validation,
        {"version": "test"},
    )
    second = (
        tmp_path
        / "reasoning"
        / "explanations.jsonl"
    ).read_text(encoding="utf-8")

    assert first == second


def test_repository_writes_valid_manifest(tmp_path) -> None:
    inference, enriched = prepare_corpus(
        tmp_path,
        make_graph(),
    )
    repository = make_repository(tmp_path)
    result = repository.build_result()
    validation = ReasoningValidator().validate(
        enriched,
        inference.inferred_edges,
        inference.traces,
        result,
    )
    repository.write_result(
        result,
        validation,
        {"version": "v0.8.7.0"},
    )
    manifest = json.loads(
        (
            tmp_path
            / "reasoning"
            / "reasoning_manifest.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["validation"]["valid"] is True
