from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tru_ai.reasoning.repository import (
    ReasoningRepository,
)
from tru_ai.reasoning.validator import (
    ReasoningValidator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_INFERRED_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph_inferred"
)

INFERENCE_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "inference"
)

REASONING_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "reasoning"
)

VERSION = "v0.8.7.0"


def build_manifest(
    *,
    generated_at: str,
    inferred_edge_count: int,
    explanation_count: int,
    proof_tree_count: int,
    unexplained_edge_count: int,
    maximum_proof_depth: int,
    graph_inferred_directory: Path,
    inference_directory: Path,
    reasoning_directory: Path,
) -> dict:
    return {
        "version": VERSION,
        "generated_at": generated_at,
        "inferred_edge_count": (
            inferred_edge_count
        ),
        "explanation_count": (
            explanation_count
        ),
        "proof_tree_count": proof_tree_count,
        "unexplained_edge_count": (
            unexplained_edge_count
        ),
        "maximum_proof_depth": (
            maximum_proof_depth
        ),
        "source_paths": {
            "graph_inferred_nodes": str(
                graph_inferred_directory
                / "nodes.jsonl"
            ),
            "graph_inferred_edges": str(
                graph_inferred_directory
                / "edges.jsonl"
            ),
            "inferred_edges": str(
                inference_directory
                / "inferred_edges.jsonl"
            ),
            "inference_traces": str(
                inference_directory
                / "inference_traces.jsonl"
            ),
        },
        "output_paths": {
            "explanations": str(
                reasoning_directory
                / "explanations.jsonl"
            ),
            "proof_trees": str(
                reasoning_directory
                / "proof_trees.jsonl"
            ),
            "reasoning_manifest": str(
                reasoning_directory
                / "reasoning_manifest.json"
            ),
        },
    }


def run_pipeline(
    *,
    graph_inferred_directory: Path = GRAPH_INFERRED_DIRECTORY,
    inference_directory: Path = INFERENCE_DIRECTORY,
    reasoning_directory: Path = REASONING_DIRECTORY,
    generated_at: str | None = None,
) -> tuple[dict, bool]:
    repository = ReasoningRepository(
        graph_inferred_directory=(
            graph_inferred_directory
        ),
        inference_directory=inference_directory,
        reasoning_directory=reasoning_directory,
    )
    graph = repository.load_graph()
    inferred_edges = repository.load_inferred_edges()
    traces = repository.load_traces()
    result = repository.build_result()
    validation = ReasoningValidator().validate(
        graph=graph,
        inferred_edges=inferred_edges,
        traces=traces,
        result=result,
    )
    maximum_depth = max(
        (
            explanation.maximum_depth
            for explanation
            in result.explanations
        ),
        default=0,
    )
    manifest = build_manifest(
        generated_at=(
            generated_at
            or datetime.now(UTC).isoformat()
        ),
        inferred_edge_count=len(
            inferred_edges
        ),
        explanation_count=len(
            result.explanations
        ),
        proof_tree_count=len(
            result.proof_trees
        ),
        unexplained_edge_count=len(
            result.unexplained_edge_ids
        ),
        maximum_proof_depth=maximum_depth,
        graph_inferred_directory=(
            graph_inferred_directory
        ),
        inference_directory=inference_directory,
        reasoning_directory=reasoning_directory,
    )
    repository.write_result(
        result=result,
        validation=validation,
        manifest=manifest,
    )
    manifest = {
        **manifest,
        "validation": validation.to_dict(),
    }

    print_summary(manifest)

    return manifest, validation.valid


def print_summary(
    manifest: dict,
) -> None:
    print()
    print(
        "TRU-AI — Deterministic Reasoning Explanations"
    )
    print("---------------------------------------------")
    print(
        "Inferred edges explained     : "
        f"{manifest['explanation_count']}"
    )
    print(
        "Proof trees generated        : "
        f"{manifest['proof_tree_count']}"
    )
    print(
        "Unexplained inferred edges   : "
        f"{manifest['unexplained_edge_count']}"
    )
    print(
        "Maximum proof depth          : "
        f"{manifest['maximum_proof_depth']}"
    )
    print(
        "Validation                   : "
        f"{manifest['validation']['valid']}"
    )


def main() -> None:
    _, valid = run_pipeline()

    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
