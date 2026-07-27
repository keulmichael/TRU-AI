from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tru_ai.exploration.indexes import ExplorationIndexes
from tru_ai.query.repository import GraphRepository
from tru_ai.reasoning.repository import ReasoningRepository


class ExplorationRepository:
    def __init__(
        self,
        graph_inferred_directory: Path,
        reasoning_directory: Path,
        exploration_directory: Path,
    ) -> None:
        self.graph_inferred_directory = graph_inferred_directory
        self.reasoning_directory = reasoning_directory
        self.exploration_directory = exploration_directory

    def load_indexes(self) -> ExplorationIndexes:
        graph = GraphRepository(
            nodes_path=self.graph_inferred_directory
            / "nodes.jsonl",
            edges_path=self.graph_inferred_directory
            / "edges.jsonl",
        ).load()
        reasoning = ReasoningRepository(
            graph_inferred_directory=(
                self.graph_inferred_directory
            ),
            inference_directory=(
                self.graph_inferred_directory.parent
                / "inference"
            ),
            reasoning_directory=self.reasoning_directory,
        )
        result = reasoning.load_reasoning_result()
        return ExplorationIndexes(
            graph,
            explanations=result.explanations,
            proof_trees=result.proof_trees,
        )

    def write_indexes(
        self,
        indexes: ExplorationIndexes,
        manifest: dict[str, Any],
    ) -> None:
        files = indexes.to_files()
        self.write_json(
            self.exploration_directory / "node_index.json",
            files["node_index"],
        )
        self.write_json(
            self.exploration_directory / "predicate_index.json",
            files["predicate_index"],
        )
        self.write_json(
            self.exploration_directory / "outgoing_index.json",
            files["outgoing_index"],
        )
        self.write_json(
            self.exploration_directory / "incoming_index.json",
            files["incoming_index"],
        )
        self.write_json(
            self.exploration_directory
            / "edge_explanation_index.json",
            files["edge_explanation_index"],
        )
        self.write_json(
            self.exploration_directory
            / "exploration_manifest.json",
            manifest,
        )

    @staticmethod
    def write_json(path: Path, record: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as output_file:
            json.dump(
                record,
                output_file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            output_file.write("\n")

    @staticmethod
    def read_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as input_file:
            return json.load(input_file)
