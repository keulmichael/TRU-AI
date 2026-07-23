import json

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)
from tru_ai.inference.engine import (
    InferenceEngine,
)
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.inference.validator import (
    InferenceValidator,
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


def make_graph() -> KnowledgeGraph:
    return KnowledgeGraph(
        nodes=(
            make_node("node-a"),
            make_node("node-b"),
            make_node("node-c"),
        ),
        edges=(
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
        ),
    )


def make_repository(
    tmp_path,
) -> InferenceRepository:
    return InferenceRepository(
        resolved_graph_directory=(
            tmp_path / "graph_resolved"
        ),
        inference_directory=(
            tmp_path / "inference"
        ),
        graph_inferred_directory=(
            tmp_path / "graph_inferred"
        ),
    )


def write_resolved_graph(
    repository: InferenceRepository,
    graph: KnowledgeGraph,
) -> None:
    repository.write_jsonl(
        repository.resolved_graph_directory
        / "nodes.jsonl",
        [
            node.to_dict()
            for node in graph.nodes
        ],
    )
    repository.write_jsonl(
        repository.resolved_graph_directory
        / "edges.jsonl",
        [
            edge.to_dict()
            for edge in graph.edges
        ],
    )


def read_jsonl(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as input_file:
        return [
            json.loads(line)
            for line in input_file
            if line.strip()
        ]


def write_outputs(tmp_path):
    graph = make_graph()
    result = InferenceEngine(
        max_depth=1
    ).run(graph)
    validation = InferenceValidator(
        max_depth=1
    ).validate(graph, result)
    repository = make_repository(tmp_path)
    manifest = {
        "version": "v0.8.6.0",
        "generated_at": "fixed",
    }
    enriched_graph = repository.write_outputs(
        source_graph=graph,
        result=result,
        validation=validation,
        manifest=manifest,
    )

    return (
        graph,
        result,
        validation,
        repository,
        enriched_graph,
    )


def test_repository_loads_resolved_graph(tmp_path) -> None:
    graph = make_graph()
    repository = make_repository(tmp_path)
    write_resolved_graph(repository, graph)

    loaded = repository.load_resolved_graph()

    assert len(loaded.nodes) == 3
    assert len(loaded.edges) == 2
    assert loaded.edges[0].confidence_max == 0.9


def test_repository_writes_expected_files(tmp_path) -> None:
    _, _, _, repository, _ = write_outputs(
        tmp_path
    )

    assert (
        repository.inference_directory
        / "inferred_edges.jsonl"
    ).exists()
    assert (
        repository.inference_directory
        / "inference_traces.jsonl"
    ).exists()
    assert (
        repository.inference_directory
        / "inference_manifest.json"
    ).exists()
    assert (
        repository.graph_inferred_directory
        / "nodes.jsonl"
    ).exists()
    assert (
        repository.graph_inferred_directory
        / "edges.jsonl"
    ).exists()
    assert (
        repository.graph_inferred_directory
        / "adjacency.json"
    ).exists()
    assert (
        repository.graph_inferred_directory
        / "inference_manifest.json"
    ).exists()


def test_repository_writes_valid_jsonl(tmp_path) -> None:
    _, result, _, repository, _ = write_outputs(
        tmp_path
    )

    records = read_jsonl(
        repository.inference_directory
        / "inferred_edges.jsonl"
    )

    assert len(records) == len(
        result.inferred_edges
    )
    assert records[0]["rule_ids"] == [
        "transitivity-is_a"
    ]


def test_repository_output_order_is_stable(tmp_path) -> None:
    _, _, _, repository, _ = write_outputs(
        tmp_path
    )

    first = (
        repository.graph_inferred_directory
        / "edges.jsonl"
    ).read_text(encoding="utf-8")

    write_outputs(tmp_path)

    second = (
        repository.graph_inferred_directory
        / "edges.jsonl"
    ).read_text(encoding="utf-8")

    assert first == second


def test_repository_does_not_modify_source_graph(tmp_path) -> None:
    graph = make_graph()
    before = [
        edge.to_dict()
        for edge in graph.edges
    ]

    result = InferenceEngine(
        max_depth=1
    ).run(graph)
    repository = make_repository(tmp_path)
    repository.write_outputs(
        source_graph=graph,
        result=result,
        validation=InferenceValidator(
            max_depth=1
        ).validate(graph, result),
        manifest={"version": "v0.8.6.0"},
    )

    after = [
        edge.to_dict()
        for edge in graph.edges
    ]

    assert before == after


def test_repository_converts_inferred_edge_to_graph_edge(tmp_path) -> None:
    _, result, _, _, _ = write_outputs(
        tmp_path
    )

    graph_edge = (
        InferenceRepository
        .inferred_edge_to_graph_edge(
            result.inferred_edges[0]
        )
    )

    assert graph_edge.relation_ids == set()
    assert graph_edge.proposition_ids == set()
    assert graph_edge.extraction_methods == {
        "deterministic_inference"
    }
    assert graph_edge.pattern_ids == {
        "transitivity-is_a"
    }


def test_enriched_graph_contains_source_and_inferred_edges(tmp_path) -> None:
    graph, result, _, _, enriched = write_outputs(
        tmp_path
    )

    assert len(enriched.nodes) == len(graph.nodes)
    assert len(enriched.edges) == (
        len(graph.edges)
        + len(result.inferred_edges)
    )

    keys = {
        (
            edge.subject_id,
            edge.predicate,
            edge.object_id,
        )
        for edge in enriched.edges
    }

    assert (
        "node-a",
        "is_a",
        "node-b",
    ) in keys
    assert (
        "node-a",
        "is_a",
        "node-c",
    ) in keys
    assert len(keys) == len(enriched.edges)


def test_repository_adjacency_contains_inferred_edge(tmp_path) -> None:
    _, _, _, repository, _ = write_outputs(
        tmp_path
    )

    adjacency = json.loads(
        (
            repository.graph_inferred_directory
            / "adjacency.json"
        ).read_text(encoding="utf-8")
    )

    outgoing = adjacency["node-a"][
        "outgoing"
    ]

    assert any(
        item["object_id"] == "node-c"
        and item["predicate"] == "is_a"
        for item in outgoing
    )


def test_repository_serialization_is_deterministic(tmp_path) -> None:
    first_path = tmp_path / "first"
    second_path = tmp_path / "second"

    write_outputs(first_path)
    write_outputs(second_path)

    first_manifest = (
        first_path
        / "inference"
        / "inference_manifest.json"
    ).read_text(encoding="utf-8")

    second_manifest = (
        second_path
        / "inference"
        / "inference_manifest.json"
    ).read_text(encoding="utf-8")

    assert first_manifest == second_manifest


def test_repository_avoids_duplicate_triplets(tmp_path) -> None:
    graph = make_graph()
    result = InferenceEngine(
        max_depth=1
    ).run(graph)
    repository = make_repository(tmp_path)

    enriched = repository.build_enriched_graph(
        source_graph=graph,
        inferred_edges=(
            result.inferred_edges[0],
            result.inferred_edges[0],
        ),
    )

    keys = [
        (
            edge.subject_id,
            edge.predicate,
            edge.object_id,
        )
        for edge in enriched.edges
    ]

    assert len(keys) == len(set(keys))
