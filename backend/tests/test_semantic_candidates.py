from tru_ai.graph.models import GraphNode
from tru_ai.semantic.candidate_generator import (
    SemanticCandidateGenerator,
)


def make_node(
    node_id: str,
    label: str,
    normalized_label: str,
    concept_id: str | None = None,
    aliases: set[str] | None = None,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=label,
        normalized_label=normalized_label,
        node_type="concept",
        concept_id=concept_id,
        category=None,
        aliases=aliases or set(),
        source_sentence_ids=set(),
        occurrence_count=1,
    )


def test_candidate_generator_matches_alias_variants():
    generator = SemanticCandidateGenerator()

    first = make_node(
        node_id="node-1",
        label="Conscience",
        normalized_label="conscience",
    )

    second = make_node(
        node_id="node-2",
        label="La conscience",
        normalized_label="la conscience",
    )

    candidates = generator.generate(
        (first, second)
    )

    assert len(candidates) == 1

    assert {
        candidates[0][0].node_id,
        candidates[0][1].node_id,
    } == {
        "node-1",
        "node-2",
    }


def test_candidate_generator_matches_same_concept_id():
    generator = SemanticCandidateGenerator()

    first = make_node(
        node_id="node-1",
        label="Conscience",
        normalized_label="conscience",
        concept_id="concept-conscience",
    )

    second = make_node(
        node_id="node-2",
        label="Conscience humaine",
        normalized_label="conscience humaine",
        concept_id="concept-conscience",
    )

    candidates = generator.generate(
        (first, second)
    )

    assert len(candidates) == 1


def test_candidate_generator_ignores_unrelated_nodes():
    generator = SemanticCandidateGenerator()

    first = make_node(
        node_id="node-1",
        label="Conscience",
        normalized_label="conscience",
    )

    second = make_node(
        node_id="node-2",
        label="Temps",
        normalized_label="temps",
    )

    candidates = generator.generate(
        (first, second)
    )

    assert candidates == []