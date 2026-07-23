from __future__ import annotations

import json
from pathlib import Path

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
    GraphNode,
)


class GraphRepository:
    """
    Charge un graphe de connaissances depuis
    les fichiers JSONL générés.
    """

    def __init__(
        self,
        nodes_path: Path,
        edges_path: Path,
    ) -> None:
        self.nodes_path = nodes_path
        self.edges_path = edges_path

    def load(self) -> KnowledgeGraph:
        nodes = self.load_nodes(
            self.nodes_path
        )

        edges = self.load_edges(
            self.edges_path
        )

        return KnowledgeGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
        )

    @staticmethod
    def load_nodes(
        path: Path,
    ) -> list[GraphNode]:
        if not path.exists():
            raise FileNotFoundError(
                "Le fichier nodes.jsonl "
                f"est absent : {path}"
            )

        nodes = []

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

                    record["aliases"] = set(
                        record.get(
                            "aliases",
                            [],
                        )
                    )

                    record[
                        "source_sentence_ids"
                    ] = set(
                        record.get(
                            "source_sentence_ids",
                            [],
                        )
                    )

                    nodes.append(
                        GraphNode(**record)
                    )
                except (
                    json.JSONDecodeError,
                    TypeError,
                    KeyError,
                ) as error:
                    raise ValueError(
                        "Nœud invalide à la ligne "
                        f"{line_number} de {path}."
                    ) from error

        return nodes

    @staticmethod
    def load_edges(
        path: Path,
    ) -> list[GraphEdge]:
        if not path.exists():
            raise FileNotFoundError(
                "Le fichier edges.jsonl "
                f"est absent : {path}"
            )

        edges = []

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

                    occurrence_count = record.get(
                        "occurrence_count",
                        0,
                    )

                    confidence_average = record.get(
                        "confidence_average",
                        0.0,
                    )

                    edge = GraphEdge(
                        edge_id=record["edge_id"],
                        subject_id=(
                            record["subject_id"]
                        ),
                        predicate=(
                            record["predicate"]
                        ),
                        object_id=(
                            record["object_id"]
                        ),
                        relation_ids=set(
                            record.get(
                                "relation_ids",
                                [],
                            )
                        ),
                        proposition_ids=set(
                            record.get(
                                "proposition_ids",
                                [],
                            )
                        ),
                        source_sentence_ids=set(
                            record.get(
                                "source_sentence_ids",
                                [],
                            )
                        ),
                        pattern_ids=set(
                            record.get(
                                "pattern_ids",
                                [],
                            )
                        ),
                        extraction_methods=set(
                            record.get(
                                "extraction_methods",
                                [],
                            )
                        ),
                        occurrence_count=(
                            occurrence_count
                        ),
                        confidence_sum=(
                            confidence_average
                            * occurrence_count
                        ),
                        confidence_max=(
                            record.get(
                                "confidence_max",
                                confidence_average,
                            )
                        ),
                    )

                    edges.append(edge)

                except (
                    json.JSONDecodeError,
                    TypeError,
                    KeyError,
                ) as error:
                    raise ValueError(
                        "Arête invalide à la ligne "
                        f"{line_number} de {path}."
                    ) from error

        return edges