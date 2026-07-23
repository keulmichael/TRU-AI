from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from tru_ai.graph.builder import (
    KnowledgeGraphBuilder,
)
from tru_ai.graph.validator import (
    KnowledgeGraphValidator,
)
from tru_ai.relations.models import Relation


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "processed"
)

GRAPH_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph"
)

RELATIONS_PATH = (
    PROCESSED_DIRECTORY / "relations.jsonl"
)

NODES_PATH = (
    GRAPH_DIRECTORY / "nodes.jsonl"
)

EDGES_PATH = (
    GRAPH_DIRECTORY / "edges.jsonl"
)

ADJACENCY_PATH = (
    GRAPH_DIRECTORY / "adjacency.json"
)

MANIFEST_PATH = (
    GRAPH_DIRECTORY / "graph_manifest.json"
)


def read_relations(
    path: Path,
) -> list[Relation]:
    if not path.exists():
        raise FileNotFoundError(
            "Le fichier relations.jsonl est absent. "
            "Exécute d'abord : "
            "python scripts\\extract_relations.py"
        )

    relations: list[Relation] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as input_file:
        for line_number, line in enumerate(
            input_file,
            start=1,
        ):
            if not line.strip():
                continue

            try:
                record = json.loads(line)

                relations.append(
                    Relation(**record)
                )
            except (
                json.JSONDecodeError,
                TypeError,
            ) as error:
                raise ValueError(
                    "Relation invalide à la ligne "
                    f"{line_number} de {path}."
                ) from error

    return relations


def write_jsonl(
    path: Path,
    records: list[dict],
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
                + "\n"
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
    relations = read_relations(
        RELATIONS_PATH
    )

    builder = KnowledgeGraphBuilder()
    validator = KnowledgeGraphValidator()

    graph = builder.build(relations)
    validation = validator.validate(graph)

    adjacency = graph.build_adjacency()

    write_jsonl(
        NODES_PATH,
        [
            node.to_dict()
            for node in graph.nodes
        ],
    )

    write_jsonl(
        EDGES_PATH,
        [
            edge.to_dict()
            for edge in graph.edges
        ],
    )

    write_json(
        ADJACENCY_PATH,
        adjacency,
    )

    node_type_counts = Counter(
        node.node_type
        for node in graph.nodes
    )

    predicate_counts = Counter(
        edge.predicate
        for edge in graph.edges
    )

    manifest = {
        "graph_version": "v0.8.5.4",
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "source_relations_path": str(
            RELATIONS_PATH
        ),
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "relation_count": len(relations),
        "node_types": dict(
            sorted(node_type_counts.items())
        ),
        "predicates": dict(
            sorted(predicate_counts.items())
        ),
        "validation": (
            validation.to_dict()
        ),
        "files": {
            "nodes": str(NODES_PATH),
            "edges": str(EDGES_PATH),
            "adjacency": str(
                ADJACENCY_PATH
            ),
        },
    }

    write_json(
        MANIFEST_PATH,
        manifest,
    )

    print()
    print("TRU-AI — Graphe de connaissances")
    print("--------------------------------")
    print(
        f"Relations sources : {len(relations)}"
    )
    print(
        f"Nœuds             : {len(graph.nodes)}"
    )
    print(
        f"Arêtes            : {len(graph.edges)}"
    )
    print(
        f"Graphe valide     : {validation.valid}"
    )
    print()
    print(f"Nœuds      : {NODES_PATH}")
    print(f"Arêtes     : {EDGES_PATH}")
    print(f"Adjacence  : {ADJACENCY_PATH}")
    print(f"Manifeste  : {MANIFEST_PATH}")
    print()

    if graph.edges:
        node_index = graph.node_index()

        print("Relations du graphe :")

        for edge in graph.edges:
            subject = node_index[
                edge.subject_id
            ]

            object_node = node_index[
                edge.object_id
            ]

            print(
                "- "
                f"{subject.label} "
                f"—[{edge.predicate}]→ "
                f"{object_node.label}"
            )

    if validation.issues:
        print()
        print("Validation :")

        for issue in validation.issues:
            resource = (
                f" ({issue.resource_id})"
                if issue.resource_id
                else ""
            )

            print(
                f"- [{issue.severity}] "
                f"{issue.message}{resource}"
            )


if __name__ == "__main__":
    main()