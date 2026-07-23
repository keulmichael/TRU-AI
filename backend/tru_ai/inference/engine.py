from __future__ import annotations

from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.inference.matcher import (
    InferenceMatcher,
    RuleMatch,
)
from tru_ai.inference.models import (
    InferenceResult,
    InferenceTrace,
    InferredEdge,
    make_inference_id,
    make_inferred_edge_id,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)


class InferenceEngine:
    def __init__(
        self,
        registry: InferenceRuleRegistry | None = None,
        max_depth: int = 2,
    ) -> None:
        self.registry = (
            registry
            or InferenceRuleRegistry.default()
        )
        self.max_depth = max_depth

    def run(
        self,
        graph: KnowledgeGraph,
    ) -> InferenceResult:
        inferred_edges: dict[
            tuple[str, str, str],
            InferredEdge,
        ] = {}
        traces: dict[
            str,
            InferenceTrace,
        ] = {}

        passes_executed = 0
        fixed_point_reached = False

        for _ in range(self.max_depth):
            passes_executed += 1
            new_edge_count = 0

            matcher = InferenceMatcher(
                graph=graph,
                inferred_edges=tuple(
                    sorted(
                        inferred_edges.values(),
                        key=lambda edge: edge.edge_id,
                    )
                ),
            )

            matches = matcher.matches(
                registry=self.registry,
                max_depth=self.max_depth,
            )

            for match in matches:
                if (
                    match.inference_depth
                    > self.max_depth
                ):
                    continue

                edge_key = match.edge_key
                edge = inferred_edges.get(
                    edge_key
                )

                if edge is None:
                    edge = self.build_edge(match)
                    inferred_edges[edge_key] = edge
                    new_edge_count += 1

                trace = self.build_trace(
                    match=match,
                    inferred_edge_id=edge.edge_id,
                )

                if (
                    trace.inference_id
                    not in traces
                ):
                    traces[
                        trace.inference_id
                    ] = trace

                    edge.register_evidence(
                        rule_id=match.rule_id,
                        premise_edge_ids=(
                            match.premise_edge_ids
                        ),
                        premise_edge_keys=(
                            match.premise_edge_keys
                        ),
                        source_sentence_ids=(
                            match.source_sentence_ids
                        ),
                        inference_depth=(
                            match.inference_depth
                        ),
                        confidence=(
                            match.confidence
                        ),
                    )

            if new_edge_count == 0:
                fixed_point_reached = True
                break

        ordered_edges = tuple(
            sorted(
                inferred_edges.values(),
                key=lambda edge: edge.edge_id,
            )
        )

        ordered_traces = tuple(
            sorted(
                traces.values(),
                key=lambda trace: (
                    trace.inference_depth,
                    trace.inference_id,
                ),
            )
        )

        max_depth_reached = (
            max(
                (
                    edge.inference_depth
                    for edge in ordered_edges
                ),
                default=0,
            )
        )

        return InferenceResult(
            inferred_edges=ordered_edges,
            traces=ordered_traces,
            passes_executed=passes_executed,
            max_depth_reached=max_depth_reached,
            fixed_point_reached=(
                fixed_point_reached
            ),
        )

    @staticmethod
    def build_edge(
        match: RuleMatch,
    ) -> InferredEdge:
        edge_id = make_inferred_edge_id(
            subject_id=match.subject_id,
            predicate=match.predicate,
            object_id=match.object_id,
        )

        return InferredEdge(
            edge_id=edge_id,
            subject_id=match.subject_id,
            predicate=match.predicate,
            object_id=match.object_id,
            inference_depth=(
                match.inference_depth
            ),
        )

    @staticmethod
    def build_trace(
        match: RuleMatch,
        inferred_edge_id: str,
    ) -> InferenceTrace:
        inference_id = make_inference_id(
            rule_id=match.rule_id,
            premise_edge_ids=(
                match.premise_edge_ids
            ),
            premise_edge_keys=(
                match.premise_edge_keys
            ),
            subject_id=match.subject_id,
            predicate=match.predicate,
            object_id=match.object_id,
            inference_depth=(
                match.inference_depth
            ),
            variable_bindings=(
                match.variable_bindings
            ),
        )

        return InferenceTrace(
            inference_id=inference_id,
            inferred_edge_id=inferred_edge_id,
            rule_id=match.rule_id,
            premise_edge_ids=(
                match.premise_edge_ids
            ),
            premise_edge_keys=(
                match.premise_edge_keys
            ),
            variable_bindings=dict(
                sorted(
                    match.variable_bindings.items()
                )
            ),
            source_sentence_ids=(
                match.source_sentence_ids
            ),
            inference_depth=(
                match.inference_depth
            ),
            confidence=match.confidence,
        )
