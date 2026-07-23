from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tru_ai.query.repository import GraphRepository
from tru_ai.semantic.graph_compactor import (
    SemanticGraphCompactor,
)
from tru_ai.semantic.resolver import (
    SemanticEntityResolver,
)
from tru_ai.semantic.validator import (
    SemanticGraphValidator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_GRAPH_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph"
)

OUTPUT_GRAPH_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph_resolved"
)

SOURCE_NODES_PATH = (
    SOURCE_GRAPH_DIRECTORY / "nodes.jsonl"
)

SOURCE_EDGES_PATH = (
    SOURCE_GRAPH_DIRECTORY / "edges.jsonl"
)

OUTPUT_NODES_PATH = (
    OUTPUT_GRAPH_DIRECTORY / "nodes.jsonl"
)

OUTPUT_EDGES_PATH = (
    OUTPUT_GRAPH_DIRECTORY / "edges.jsonl"
)

OUTPUT_ADJACENCY_PATH = (
    OUTPUT_GRAPH_DIRECTORY / "adjacency.json"
)

OUTPUT_DECISIONS_PATH = (
    OUTPUT_GRAPH_DIRECTORY / "merge_decisions.jsonl"
)

OUTPUT_UNRESOLVED_PATH = (
    OUTPUT_GRAPH_DIRECTORY
    / "unresolved_candidates.jsonl"
)

OUTPUT_MANIFEST_PATH = (
    OUTPUT_GRAPH_DIRECTORY
    / "resolution_manifest.json"
)


def write_json(
    path: Path,
    record: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            record,
            output_file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

        output_file.write("\n")


def write_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for record in records:
            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

            output_file.write("\n")


def build_adjacency(
    nodes,
    edges,
) -> dict[str, dict[str, list[dict[str, str]]]]:
    adjacency: dict[
        str,
        dict[str, list[dict[str, str]]],
    ] = {}

    for node in nodes:
        adjacency[node.node_id] = {
            "outgoing": [],
            "incoming": [],
        }

    for edge in edges:
        adjacency.setdefault(
            edge.subject_id,
            {
                "outgoing": [],
                "incoming": [],
            },
        )

        adjacency.setdefault(
            edge.object_id,
            {
                "outgoing": [],
                "incoming": [],
            },
        )

        adjacency[
            edge.subject_id
        ]["outgoing"].append(
            {
                "edge_id": edge.edge_id,
                "predicate": edge.predicate,
                "node_id": edge.object_id,
            }
        )

        adjacency[
            edge.object_id
        ]["incoming"].append(
            {
                "edge_id": edge.edge_id,
                "predicate": edge.predicate,
                "node_id": edge.subject_id,
            }
        )

    for node_adjacency in adjacency.values():
        node_adjacency["outgoing"].sort(
            key=lambda item: (
                item["predicate"],
                item["node_id"],
                item["edge_id"],
            )
        )

        node_adjacency["incoming"].sort(
            key=lambda item: (
                item["predicate"],
                item["node_id"],
                item["edge_id"],
            )
        )

    return dict(sorted(adjacency.items()))


def main() -> None:
    print()
    print("TRU-AI — Résolution sémantique")
    print("------------------------------")

    repository = GraphRepository(
        nodes_path=SOURCE_NODES_PATH,
        edges_path=SOURCE_EDGES_PATH,
    )

    original_graph = repository.load()

    resolver = SemanticEntityResolver()

    resolution = resolver.resolve(
        original_graph.nodes
    )

    compactor = SemanticGraphCompactor()

    resolved_graph = compactor.compact(
        graph=original_graph,
        resolution=resolution,
    )

    validator = SemanticGraphValidator()

    validation = validator.validate(
        original_graph=original_graph,
        resolved_graph=resolved_graph,
        resolution=resolution,
    )

    merge_decisions = [
        decision
        for decision in resolution.decisions
        if decision.decision == "merge"
    ]

    unresolved_candidates = list(
        resolution.unresolved_candidates
    )

    merged_node_count = (
        len(original_graph.nodes)
        - len(resolved_graph.nodes)
    )

    adjacency = build_adjacency(
        nodes=resolved_graph.nodes,
        edges=resolved_graph.edges,
    )

    write_jsonl(
        OUTPUT_NODES_PATH,
        [
            node.to_dict()
            for node in resolved_graph.nodes
        ],
    )

    write_jsonl(
        OUTPUT_EDGES_PATH,
        [
            edge.to_dict()
            for edge in resolved_graph.edges
        ],
    )

    write_json(
        OUTPUT_ADJACENCY_PATH,
        adjacency,
    )

    write_jsonl(
        OUTPUT_DECISIONS_PATH,
        [
            decision.to_dict()
            for decision in resolution.decisions
        ],
    )

    write_jsonl(
        OUTPUT_UNRESOLVED_PATH,
        [
            decision.to_dict()
            for decision
            in unresolved_candidates
        ],
    )

    manifest = {
        "version": "v0.8.5.6",
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "source": {
            "nodes": str(SOURCE_NODES_PATH),
            "edges": str(SOURCE_EDGES_PATH),
        },
        "outputs": {
            "nodes": str(OUTPUT_NODES_PATH),
            "edges": str(OUTPUT_EDGES_PATH),
            "adjacency": str(
                OUTPUT_ADJACENCY_PATH
            ),
            "merge_decisions": str(
                OUTPUT_DECISIONS_PATH
            ),
            "unresolved_candidates": str(
                OUTPUT_UNRESOLVED_PATH
            ),
        },
        "original_node_count": len(
            original_graph.nodes
        ),
        "resolved_node_count": len(
            resolved_graph.nodes
        ),
        "merged_node_count": merged_node_count,
        "original_edge_count": len(
            original_graph.edges
        ),
        "resolved_edge_count": len(
            resolved_graph.edges
        ),
        "automatic_merge_count": len(
            merge_decisions
        ),
        "review_candidate_count": len(
            unresolved_candidates
        ),
        "decision_count": len(
            resolution.decisions
        ),
        "validation": validation.to_dict(),
    }

    write_json(
        OUTPUT_MANIFEST_PATH,
        manifest,
    )

    print(
        f"Nœuds originaux       : "
        f"{len(original_graph.nodes)}"
    )

    print(
        f"Nœuds résolus         : "
        f"{len(resolved_graph.nodes)}"
    )

    print(
        f"Nœuds fusionnés       : "
        f"{merged_node_count}"
    )

    print(
        f"Arêtes originales     : "
        f"{len(original_graph.edges)}"
    )

    print(
        f"Arêtes résolues       : "
        f"{len(resolved_graph.edges)}"
    )

    print(
        f"Fusions automatiques  : "
        f"{len(merge_decisions)}"
    )

    print(
        f"Candidats à examiner  : "
        f"{len(unresolved_candidates)}"
    )

    print(
        f"Validation            : "
        f"{validation.valid}"
    )

    print()
    print(
        f"Graphe résolu : "
        f"{OUTPUT_GRAPH_DIRECTORY}"
    )

    if validation.errors:
        print()
        print("Erreurs de validation :")

        for error in validation.errors:
            print(f"- {error}")

    if validation.warnings:
        print()
        print("Avertissements :")

        for warning in validation.warnings:
            print(f"- {warning}")

    if not validation.valid:
        raise RuntimeError(
            "La validation du graphe résolu "
            "a échoué."
        )


if __name__ == "__main__":
    main()