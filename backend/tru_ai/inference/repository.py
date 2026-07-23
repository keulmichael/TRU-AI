from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import (
    GraphEdge,
)
from tru_ai.inference.models import (
    InferenceResult,
    InferenceValidationReport,
    InferredEdge,
)
from tru_ai.query.repository import GraphRepository


class InferenceRepository:
    def __init__(
        self,
        resolved_graph_directory: Path,
        inference_directory: Path,
        graph_inferred_directory: Path,
    ) -> None:
        self.resolved_graph_directory = (
            resolved_graph_directory
        )
        self.inference_directory = (
            inference_directory
        )
        self.graph_inferred_directory = (
            graph_inferred_directory
        )

    def load_resolved_graph(
        self,
    ) -> KnowledgeGraph:
        repository = GraphRepository(
            nodes_path=(
                self.resolved_graph_directory
                / "nodes.jsonl"
            ),
            edges_path=(
                self.resolved_graph_directory
                / "edges.jsonl"
            ),
        )

        return repository.load()

    def write_outputs(
        self,
        source_graph: KnowledgeGraph,
        result: InferenceResult,
        validation: InferenceValidationReport,
        manifest: dict[str, Any],
    ) -> KnowledgeGraph:
        enriched_graph = self.build_enriched_graph(
            source_graph=source_graph,
            inferred_edges=result.inferred_edges,
        )

        inference_manifest = {
            **manifest,
            "validation": validation.to_dict(),
        }

        self.write_jsonl(
            self.inference_directory
            / "inferred_edges.jsonl",
            [
                edge.to_dict()
                for edge in result.inferred_edges
            ],
        )

        self.write_jsonl(
            self.inference_directory
            / "inference_traces.jsonl",
            [
                trace.to_dict()
                for trace in result.traces
            ],
        )

        self.write_json(
            self.inference_directory
            / "inference_manifest.json",
            inference_manifest,
        )

        self.write_jsonl(
            self.graph_inferred_directory
            / "nodes.jsonl",
            [
                node.to_dict()
                for node in enriched_graph.nodes
            ],
        )

        self.write_jsonl(
            self.graph_inferred_directory
            / "edges.jsonl",
            [
                edge.to_dict()
                for edge in enriched_graph.edges
            ],
        )

        self.write_json(
            self.graph_inferred_directory
            / "adjacency.json",
            enriched_graph.build_adjacency(),
        )

        self.write_json(
            self.graph_inferred_directory
            / "inference_manifest.json",
            inference_manifest,
        )

        return enriched_graph

    @staticmethod
    def build_enriched_graph(
        source_graph: KnowledgeGraph,
        inferred_edges: tuple[InferredEdge, ...],
    ) -> KnowledgeGraph:
        source_edge_keys = {
            (
                edge.subject_id,
                edge.predicate,
                edge.object_id,
            )
            for edge in source_graph.edges
        }

        converted_edges: list[GraphEdge] = []
        inferred_edge_keys: set[
            tuple[str, str, str]
        ] = set()

        for inferred_edge in sorted(
            inferred_edges,
            key=lambda edge: edge.edge_id,
        ):
            key = (
                inferred_edge.subject_id,
                inferred_edge.predicate,
                inferred_edge.object_id,
            )

            if key in source_edge_keys:
                continue

            if key in inferred_edge_keys:
                continue

            inferred_edge_keys.add(key)
            converted_edges.append(
                InferenceRepository
                .inferred_edge_to_graph_edge(
                    inferred_edge
                )
            )

        edges = tuple(
            sorted(
                (
                    *source_graph.edges,
                    *converted_edges,
                ),
                key=lambda edge: edge.edge_id,
            )
        )

        return KnowledgeGraph(
            nodes=tuple(source_graph.nodes),
            edges=edges,
        )

    @staticmethod
    def inferred_edge_to_graph_edge(
        inferred_edge: InferredEdge,
    ) -> GraphEdge:
        return GraphEdge(
            edge_id=inferred_edge.edge_id,
            subject_id=inferred_edge.subject_id,
            predicate=inferred_edge.predicate,
            object_id=inferred_edge.object_id,
            relation_ids=set(),
            proposition_ids=set(),
            source_sentence_ids=set(
                inferred_edge.source_sentence_ids
            ),
            pattern_ids=set(
                inferred_edge.rule_ids
            ),
            extraction_methods={
                "deterministic_inference"
            },
            occurrence_count=(
                inferred_edge.occurrence_count
            ),
            confidence_sum=(
                inferred_edge.confidence_sum
            ),
            confidence_max=(
                inferred_edge.confidence_max
            ),
        )

    @staticmethod
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
                )
                output_file.write("\n")

    @staticmethod
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
