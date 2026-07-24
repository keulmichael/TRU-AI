from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tru_ai.inference.models import (
    InferenceTrace,
    InferredEdge,
)
from tru_ai.query.repository import GraphRepository
from tru_ai.reasoning.explainer import (
    ReasoningExplainer,
)
from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
    ReasoningResult,
    ReasoningValidationReport,
)
from tru_ai.reasoning.proof_builder import (
    ProofBuilder,
)


class ReasoningRepository:
    def __init__(
        self,
        graph_inferred_directory: Path,
        inference_directory: Path,
        reasoning_directory: Path,
    ) -> None:
        self.graph_inferred_directory = (
            graph_inferred_directory
        )
        self.inference_directory = (
            inference_directory
        )
        self.reasoning_directory = (
            reasoning_directory
        )

    def build_result(
        self,
    ) -> ReasoningResult:
        graph = self.load_graph()
        inferred_edges = (
            self.load_inferred_edges()
        )
        traces = self.load_traces()

        proof_trees, unexplained = ProofBuilder(
            graph=graph,
            inferred_edges=inferred_edges,
            traces=traces,
        ).build_all()

        explanations = ReasoningExplainer(
            graph=graph,
            inferred_edges=inferred_edges,
            traces=traces,
        ).explain_all(proof_trees)

        return ReasoningResult(
            explanations=explanations,
            proof_trees=proof_trees,
            explained_edge_count=len(
                explanations
            ),
            unexplained_edge_ids=unexplained,
        )

    def load_graph(self):
        return GraphRepository(
            nodes_path=(
                self.graph_inferred_directory
                / "nodes.jsonl"
            ),
            edges_path=(
                self.graph_inferred_directory
                / "edges.jsonl"
            ),
        ).load()

    def load_inferred_edges(
        self,
    ) -> tuple[InferredEdge, ...]:
        path = (
            self.inference_directory
            / "inferred_edges.jsonl"
        )

        records = self.read_jsonl(path)
        edges: list[InferredEdge] = []

        for record in records:
            edges.append(
                InferredEdge(
                    edge_id=record["edge_id"],
                    subject_id=record["subject_id"],
                    predicate=record["predicate"],
                    object_id=record["object_id"],
                    rule_ids=set(
                        record.get(
                            "rule_ids",
                            [],
                        )
                    ),
                    premise_edge_ids=set(
                        record.get(
                            "premise_edge_ids",
                            [],
                        )
                    ),
                    premise_edge_keys={
                        tuple(edge_key)
                        for edge_key in record.get(
                            "premise_edge_keys",
                            [],
                        )
                    },
                    source_sentence_ids=set(
                        record.get(
                            "source_sentence_ids",
                            [],
                        )
                    ),
                    inference_depth=record[
                        "inference_depth"
                    ],
                    occurrence_count=record[
                        "occurrence_count"
                    ],
                    confidence_sum=record[
                        "confidence_sum"
                    ],
                    confidence_max=record[
                        "confidence_max"
                    ],
                )
            )

        return tuple(
            sorted(
                edges,
                key=lambda edge: edge.edge_id,
            )
        )

    def load_traces(
        self,
    ) -> tuple[InferenceTrace, ...]:
        path = (
            self.inference_directory
            / "inference_traces.jsonl"
        )
        traces: list[InferenceTrace] = []

        for record in self.read_jsonl(path):
            traces.append(
                InferenceTrace(
                    inference_id=record[
                        "inference_id"
                    ],
                    inferred_edge_id=record[
                        "inferred_edge_id"
                    ],
                    rule_id=record["rule_id"],
                    premise_edge_ids=tuple(
                        record.get(
                            "premise_edge_ids",
                            [],
                        )
                    ),
                    premise_edge_keys=tuple(
                        tuple(edge_key)
                        for edge_key
                        in record.get(
                            "premise_edge_keys",
                            [],
                        )
                    ),
                    variable_bindings=dict(
                        record.get(
                            "variable_bindings",
                            {},
                        )
                    ),
                    source_sentence_ids=tuple(
                        record.get(
                            "source_sentence_ids",
                            [],
                        )
                    ),
                    inference_depth=record[
                        "inference_depth"
                    ],
                    confidence=record[
                        "confidence"
                    ],
                )
            )

        return tuple(
            sorted(
                traces,
                key=lambda trace: (
                    trace.inference_depth,
                    trace.inference_id,
                ),
            )
        )

    def write_result(
        self,
        result: ReasoningResult,
        validation: ReasoningValidationReport,
        manifest: dict[str, Any],
    ) -> None:
        complete_manifest = {
            **manifest,
            "validation": validation.to_dict(),
        }

        self.write_jsonl(
            self.reasoning_directory
            / "explanations.jsonl",
            [
                explanation.to_dict()
                for explanation
                in result.explanations
            ],
        )
        self.write_jsonl(
            self.reasoning_directory
            / "proof_trees.jsonl",
            [
                proof_tree.to_dict()
                for proof_tree
                in result.proof_trees
            ],
        )
        self.write_json(
            self.reasoning_directory
            / "reasoning_manifest.json",
            complete_manifest,
        )

    @staticmethod
    def read_jsonl(
        path: Path,
    ) -> list[dict]:
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier absent : {path}"
            )

        records: list[dict] = []

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
                    records.append(
                        json.loads(line)
                    )
                except json.JSONDecodeError as error:
                    raise ValueError(
                        "JSONL invalide ligne "
                        f"{line_number} : {path}"
                    ) from error

        return records

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

    def load_reasoning_result(
        self,
    ) -> ReasoningResult:
        explanations = tuple(
            self.parse_explanation(record)
            for record in self.read_jsonl(
                self.reasoning_directory
                / "explanations.jsonl"
            )
        )
        proof_trees = tuple(
            self.parse_proof_tree(record)
            for record in self.read_jsonl(
                self.reasoning_directory
                / "proof_trees.jsonl"
            )
        )
        explained_ids = tuple(
            explanation.inferred_edge_id
            for explanation in explanations
        )
        inferred_ids = tuple(
            edge.edge_id
            for edge
            in self.load_inferred_edges()
        )
        unexplained = tuple(
            sorted(
                set(inferred_ids)
                - set(explained_ids)
            )
        )

        return ReasoningResult(
            explanations=explanations,
            proof_trees=proof_trees,
            explained_edge_count=len(
                explanations
            ),
            unexplained_edge_ids=unexplained,
        )

    @staticmethod
    def parse_explanation(
        record: dict,
    ) -> ReasoningExplanation:
        from tru_ai.reasoning.models import (
            ReasoningStep,
        )

        return ReasoningExplanation(
            explanation_id=record[
                "explanation_id"
            ],
            inferred_edge_id=record[
                "inferred_edge_id"
            ],
            conclusion_edge_key=tuple(
                record["conclusion_edge_key"]
            ),
            rule_ids=tuple(
                record.get("rule_ids", [])
            ),
            steps=tuple(
                ReasoningStep(
                    step_id=step["step_id"],
                    step_number=step[
                        "step_number"
                    ],
                    edge_id=step["edge_id"],
                    edge_key=tuple(
                        step["edge_key"]
                    ),
                    role=step["role"],
                    depth=step["depth"],
                    confidence=step[
                        "confidence"
                    ],
                    source_sentence_ids=tuple(
                        step.get(
                            "source_sentence_ids",
                            [],
                        )
                    ),
                )
                for step in record.get(
                    "steps",
                    [],
                )
            ),
            proof_tree_id=record[
                "proof_tree_id"
            ],
            maximum_depth=record[
                "maximum_depth"
            ],
            confidence=record["confidence"],
            deterministic_text=record[
                "deterministic_text"
            ],
        )

    @staticmethod
    def parse_proof_tree(
        record: dict,
    ) -> ProofTreeNode:
        return ProofTreeNode(
            node_id=record["node_id"],
            edge_id=record["edge_id"],
            edge_key=tuple(
                record["edge_key"]
            ),
            node_type=record["node_type"],
            rule_id=record.get("rule_id"),
            confidence=record["confidence"],
            depth=record["depth"],
            children=tuple(
                ReasoningRepository
                .parse_proof_tree(child)
                for child in record.get(
                    "children",
                    [],
                )
            ),
        )
