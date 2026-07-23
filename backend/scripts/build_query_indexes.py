from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from tru_ai.query.graph_index import GraphIndex
from tru_ai.query.repository import (
    GraphRepository,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph"
)

NODES_PATH = (
    GRAPH_DIRECTORY / "nodes.jsonl"
)

EDGES_PATH = (
    GRAPH_DIRECTORY / "edges.jsonl"
)

QUERY_INDEX_PATH = (
    GRAPH_DIRECTORY / "query_index.json"
)

QUERY_MANIFEST_PATH = (
    GRAPH_DIRECTORY
    / "query_manifest.json"
)


def write_json(
    path: Path,
    record: dict,
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


def main() -> None:
    repository = GraphRepository(
        nodes_path=NODES_PATH,
        edges_path=EDGES_PATH,
    )

    graph = repository.load()
    index = GraphIndex(graph)

    write_json(
        QUERY_INDEX_PATH,
        index.to_dict(),
    )

    manifest = {
        "query_version": "v0.8.5.5",
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "label_index_count": len(
            index.node_ids_by_label
        ),
        "alias_index_count": len(
            index.node_ids_by_alias
        ),
        "predicate_index_count": len(
            index.edge_ids_by_predicate
        ),
        "files": {
            "nodes": str(NODES_PATH),
            "edges": str(EDGES_PATH),
            "query_index": str(
                QUERY_INDEX_PATH
            ),
        },
    }

    write_json(
        QUERY_MANIFEST_PATH,
        manifest,
    )

    print()
    print("TRU-AI — Index de requêtes")
    print("--------------------------")
    print(
        f"Nœuds              : "
        f"{len(graph.nodes)}"
    )
    print(
        f"Arêtes             : "
        f"{len(graph.edges)}"
    )
    print(
        f"Étiquettes indexées: "
        f"{len(index.node_ids_by_label)}"
    )
    print(
        f"Alias indexés      : "
        f"{len(index.node_ids_by_alias)}"
    )
    print(
        f"Prédicats indexés  : "
        f"{len(index.edge_ids_by_predicate)}"
    )
    print()
    print(
        f"Index     : {QUERY_INDEX_PATH}"
    )
    print(
        f"Manifeste : {QUERY_MANIFEST_PATH}"
    )


if __name__ == "__main__":
    main()