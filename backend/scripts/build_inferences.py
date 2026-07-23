from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tru_ai.inference.engine import (
    InferenceEngine,
)
from tru_ai.inference.repository import (
    InferenceRepository,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)
from tru_ai.inference.validator import (
    InferenceValidator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_GRAPH_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph_resolved"
)

INFERENCE_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "inference"
)

GRAPH_INFERRED_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph_inferred"
)

MAX_DEPTH = 2
VERSION = "v0.8.6.0"


def build_manifest(
    *,
    generated_at: str,
    source_graph_directory: Path,
    inference_directory: Path,
    graph_inferred_directory: Path,
    original_node_count: int,
    original_edge_count: int,
    inferred_edge_count: int,
    trace_count: int,
    enriched_edge_count: int,
    active_rule_count: int,
    passes_executed: int,
    max_depth_configured: int,
    max_depth_reached: int,
    fixed_point_reached: bool,
) -> dict:
    return {
        "version": VERSION,
        "generated_at": generated_at,
        "source": {
            "nodes": str(
                source_graph_directory
                / "nodes.jsonl"
            ),
            "edges": str(
                source_graph_directory
                / "edges.jsonl"
            ),
        },
        "outputs": {
            "inferred_edges": str(
                inference_directory
                / "inferred_edges.jsonl"
            ),
            "inference_traces": str(
                inference_directory
                / "inference_traces.jsonl"
            ),
            "inference_manifest": str(
                inference_directory
                / "inference_manifest.json"
            ),
            "graph_inferred_nodes": str(
                graph_inferred_directory
                / "nodes.jsonl"
            ),
            "graph_inferred_edges": str(
                graph_inferred_directory
                / "edges.jsonl"
            ),
            "graph_inferred_adjacency": str(
                graph_inferred_directory
                / "adjacency.json"
            ),
            "graph_inferred_manifest": str(
                graph_inferred_directory
                / "inference_manifest.json"
            ),
        },
        "original_node_count": original_node_count,
        "original_edge_count": original_edge_count,
        "inferred_edge_count": inferred_edge_count,
        "trace_count": trace_count,
        "enriched_edge_count": enriched_edge_count,
        "active_rule_count": active_rule_count,
        "passes_executed": passes_executed,
        "max_depth_configured": max_depth_configured,
        "max_depth_reached": max_depth_reached,
        "fixed_point_reached": fixed_point_reached,
    }


def run_pipeline(
    *,
    source_graph_directory: Path = SOURCE_GRAPH_DIRECTORY,
    inference_directory: Path = INFERENCE_DIRECTORY,
    graph_inferred_directory: Path = GRAPH_INFERRED_DIRECTORY,
    max_depth: int = MAX_DEPTH,
    generated_at: str | None = None,
) -> tuple[dict, bool]:
    repository = InferenceRepository(
        resolved_graph_directory=(
            source_graph_directory
        ),
        inference_directory=inference_directory,
        graph_inferred_directory=(
            graph_inferred_directory
        ),
    )

    graph = repository.load_resolved_graph()

    registry = InferenceRuleRegistry.default()
    engine = InferenceEngine(
        registry=registry,
        max_depth=max_depth,
    )

    result = engine.run(graph)

    validator = InferenceValidator(
        registry=registry,
        max_depth=max_depth,
    )
    validation = validator.validate(
        graph,
        result,
    )

    enriched_graph = (
        repository.build_enriched_graph(
            source_graph=graph,
            inferred_edges=(
                result.inferred_edges
            ),
        )
    )

    manifest = build_manifest(
        generated_at=(
            generated_at
            or datetime.now(UTC).isoformat()
        ),
        source_graph_directory=(
            source_graph_directory
        ),
        inference_directory=(
            inference_directory
        ),
        graph_inferred_directory=(
            graph_inferred_directory
        ),
        original_node_count=len(graph.nodes),
        original_edge_count=len(graph.edges),
        inferred_edge_count=len(
            result.inferred_edges
        ),
        trace_count=len(result.traces),
        enriched_edge_count=len(
            enriched_graph.edges
        ),
        active_rule_count=len(
            registry.active_rules()
        ),
        passes_executed=(
            result.passes_executed
        ),
        max_depth_configured=max_depth,
        max_depth_reached=(
            result.max_depth_reached
        ),
        fixed_point_reached=(
            result.fixed_point_reached
        ),
    )

    repository.write_outputs(
        source_graph=graph,
        result=result,
        validation=validation,
        manifest=manifest,
    )

    manifest = {
        **manifest,
        "validation": validation.to_dict(),
    }

    print_summary(
        manifest=manifest,
    )

    return (
        manifest,
        validation.valid,
    )


def print_summary(
    manifest: dict,
) -> None:
    print()
    print(
        "TRU-AI — Deterministic Inference Engine"
    )
    print("--------------------------------------")
    print(
        "Nodes loaded               : "
        f"{manifest['original_node_count']}"
    )
    print(
        "Source edges               : "
        f"{manifest['original_edge_count']}"
    )
    print(
        "Active rules               : "
        f"{manifest['active_rule_count']}"
    )
    print(
        "Inference passes           : "
        f"{manifest['passes_executed']}"
    )
    print(
        "Inferred edges             : "
        f"{manifest['inferred_edge_count']}"
    )
    print(
        "Inference traces           : "
        f"{manifest['trace_count']}"
    )
    print(
        "Maximum depth reached      : "
        f"{manifest['max_depth_reached']}"
    )
    print(
        "Fixed point reached        : "
        f"{manifest['fixed_point_reached']}"
    )
    print(
        "Validation                 : "
        f"{manifest['validation']['valid']}"
    )


def main() -> None:
    _, valid = run_pipeline()

    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
