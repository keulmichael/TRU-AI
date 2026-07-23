import json

from tru_ai.query.repository import (
    GraphRepository,
)


def test_repository_loads_graph(
    tmp_path,
) -> None:
    nodes_path = (
        tmp_path / "nodes.jsonl"
    )

    edges_path = (
        tmp_path / "edges.jsonl"
    )

    node_records = [
        {
            "node_id": "node-a",
            "label": "A",
            "normalized_label": "a",
            "node_type": "entity",
            "concept_id": None,
            "category": None,
            "aliases": ["A"],
            "source_sentence_ids": [
                "sentence-001"
            ],
            "occurrence_count": 1,
        },
        {
            "node_id": "node-b",
            "label": "B",
            "normalized_label": "b",
            "node_type": "entity",
            "concept_id": None,
            "category": None,
            "aliases": ["B"],
            "source_sentence_ids": [
                "sentence-001"
            ],
            "occurrence_count": 1,
        },
    ]

    edge_record = {
        "edge_id": "edge-ab",
        "subject_id": "node-a",
        "predicate": "relie",
        "object_id": "node-b",
        "relation_ids": [
            "relation-001"
        ],
        "proposition_ids": [
            "proposition-001"
        ],
        "source_sentence_ids": [
            "sentence-001"
        ],
        "pattern_ids": [
            "transitive_verb"
        ],
        "extraction_methods": [
            "deterministic_pattern"
        ],
        "occurrence_count": 1,
        "confidence_average": 0.92,
        "confidence_max": 0.92,
    }

    with nodes_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for record in node_records:
            output_file.write(
                json.dumps(record) + "\n"
            )

    with edges_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        output_file.write(
            json.dumps(edge_record) + "\n"
        )

    repository = GraphRepository(
        nodes_path=nodes_path,
        edges_path=edges_path,
    )

    graph = repository.load()

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert (
        graph.edges[0].confidence_average
        == 0.92
    )