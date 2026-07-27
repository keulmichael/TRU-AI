from tru_ai.exploration.indexes import (
    ExplorationIndexes,
)
from tru_ai.graph.builder import KnowledgeGraph
from tru_ai.graph.models import GraphEdge, GraphNode
from tru_ai.reasoning.models import (
    ReasoningExplanation,
)


def make_graph() -> KnowledgeGraph:
    nodes = (
        GraphNode(
            "node-a",
            "Alpha",
            "alpha",
            "concept",
            aliases={"A"},
        ),
        GraphNode(
            "node-b",
            "Beta",
            "beta",
            "concept",
        ),
    )
    edges = (
        GraphEdge(
            edge_id="edge-1",
            subject_id="node-a",
            predicate="contains",
            object_id="node-b",
            occurrence_count=1,
            confidence_sum=0.9,
            confidence_max=0.9,
        ),
        GraphEdge(
            edge_id="inferred-edge-1",
            subject_id="node-b",
            predicate="part_of",
            object_id="node-a",
            extraction_methods={
                "deterministic_inference"
            },
            occurrence_count=1,
            confidence_sum=0.9,
            confidence_max=0.9,
        ),
    )
    return KnowledgeGraph(nodes, edges)


def test_indexes_are_sorted() -> None:
    indexes = ExplorationIndexes(make_graph())

    assert indexes.outgoing_edge_ids[
        "node-a"
    ] == ["edge-1"]
    assert indexes.incoming_edge_ids[
        "node-a"
    ] == ["inferred-edge-1"]
    assert indexes.edge_ids_by_predicate[
        "contains"
    ] == ["edge-1"]


def test_index_searches_nodes() -> None:
    indexes = ExplorationIndexes(make_graph())

    results = indexes.search_nodes(
        "alp",
        limit=10,
    )

    assert results[0]["node_id"] == "node-a"


def test_index_marks_inferred_edges_and_explanations() -> None:
    explanation = ReasoningExplanation(
        explanation_id="explanation-1",
        inferred_edge_id="inferred-edge-1",
        conclusion_edge_key=(
            "node-b",
            "part_of",
            "node-a",
        ),
        rule_ids=("rule-1",),
        steps=(),
        proof_tree_id="proof-tree-1",
        maximum_depth=1,
        confidence=0.9,
        deterministic_text="text",
    )
    indexes = ExplorationIndexes(
        make_graph(),
        explanations=(explanation,),
    )
    record = indexes.edge_to_dict(
        "inferred-edge-1"
    )

    assert record["inferred"] is True
    assert record["explanation_id"] == "explanation-1"


def test_index_to_files_is_deterministic() -> None:
    indexes = ExplorationIndexes(make_graph())

    assert indexes.to_files() == indexes.to_files()
