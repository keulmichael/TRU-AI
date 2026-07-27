from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tru_ai.exploration.repository import ExplorationRepository
from tru_ai.exploration.validator import ExplorationValidator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPH_INFERRED_DIRECTORY = PROJECT_ROOT / "corpus" / "graph_inferred"
REASONING_DIRECTORY = PROJECT_ROOT / "corpus" / "reasoning"
EXPLORATION_DIRECTORY = PROJECT_ROOT / "corpus" / "exploration"
VERSION = "v0.8.8.0"


def build_manifest(
    *,
    generated_at: str,
    indexes,
    validation,
) -> dict:
    source_edges = [
        edge
        for edge in indexes.graph.edges
        if not indexes.is_inferred_edge(edge)
    ]
    inferred_edges = [
        edge
        for edge in indexes.graph.edges
        if indexes.is_inferred_edge(edge)
    ]
    return {
        "version": VERSION,
        "generated_at": generated_at,
        "node_count": len(indexes.nodes_by_id),
        "edge_count": len(indexes.edges_by_id),
        "predicate_count": len(indexes.edge_ids_by_predicate),
        "source_edge_count": len(source_edges),
        "inferred_edge_count": len(inferred_edges),
        "explanation_count": len(indexes.explanations_by_edge_id),
        "index_file_count": 5,
        "validation": validation.to_dict(),
        "source_paths": {
            "graph_inferred_nodes": str(
                GRAPH_INFERRED_DIRECTORY / "nodes.jsonl"
            ),
            "graph_inferred_edges": str(
                GRAPH_INFERRED_DIRECTORY / "edges.jsonl"
            ),
            "reasoning_explanations": str(
                REASONING_DIRECTORY / "explanations.jsonl"
            ),
            "reasoning_proof_trees": str(
                REASONING_DIRECTORY / "proof_trees.jsonl"
            ),
        },
        "output_paths": {
            "node_index": str(EXPLORATION_DIRECTORY / "node_index.json"),
            "predicate_index": str(EXPLORATION_DIRECTORY / "predicate_index.json"),
            "outgoing_index": str(EXPLORATION_DIRECTORY / "outgoing_index.json"),
            "incoming_index": str(EXPLORATION_DIRECTORY / "incoming_index.json"),
            "edge_explanation_index": str(
                EXPLORATION_DIRECTORY / "edge_explanation_index.json"
            ),
            "manifest": str(
                EXPLORATION_DIRECTORY / "exploration_manifest.json"
            ),
        },
    }


def run_pipeline(generated_at: str | None = None) -> tuple[dict, bool]:
    repository = ExplorationRepository(
        GRAPH_INFERRED_DIRECTORY,
        REASONING_DIRECTORY,
        EXPLORATION_DIRECTORY,
    )
    indexes = repository.load_indexes()
    validation = ExplorationValidator().validate_indexes(indexes)
    manifest = build_manifest(
        generated_at=generated_at or datetime.now(UTC).isoformat(),
        indexes=indexes,
        validation=validation,
    )
    repository.write_indexes(indexes, manifest)
    print()
    print("TRU-AI — Advanced Query and Graph Exploration")
    print("----------------------------------------------")
    print(f"Nodes indexed               : {manifest['node_count']}")
    print(f"Edges indexed               : {manifest['edge_count']}")
    print(f"Predicates indexed          : {manifest['predicate_count']}")
    print(f"Explanations indexed        : {manifest['explanation_count']}")
    print(f"Validation                  : {validation.valid}")
    return manifest, validation.valid


def main() -> None:
    _, valid = run_pipeline()
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
