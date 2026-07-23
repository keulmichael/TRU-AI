import inspect

import tru_ai.inference.rule as rule_module
from tru_ai.graph.models import GraphEdge
from tru_ai.inference.models import (
    InferenceRule,
)
from tru_ai.inference.rule import (
    apply_inverse_rule,
    apply_symmetry_rule,
    apply_transitivity_rule,
    calculate_confidence,
)
from tru_ai.inference.rule_registry import (
    InferenceRuleRegistry,
)


def make_edge(
    edge_id: str,
    subject_id: str,
    predicate: str,
    object_id: str,
    confidence: float = 0.9,
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        source_sentence_ids={
            f"sentence-{edge_id}"
        },
        occurrence_count=1,
        confidence_sum=confidence,
        confidence_max=confidence,
    )


def test_registry_contains_all_v1_rules() -> None:
    registry = InferenceRuleRegistry.default()
    rule_ids = {
        rule.rule_id
        for rule in registry.rules
    }

    assert {
        "transitivity-is_a",
        "transitivity-part_of",
        "transitivity-depends_on",
        "transitivity-implies",
        "inverse-contains-to-part_of",
        "inverse-part_of-to-contains",
        "inverse-causes-to-caused_by",
        "inverse-caused_by-to-causes",
        "inverse-precedes-to-follows",
        "inverse-follows-to-precedes",
        "inverse-includes-to-included_in",
        "inverse-included_in-to-includes",
        "symmetry-equivalent_to",
        "symmetry-related_to",
        "symmetry-interacts_with",
    }.issubset(rule_ids)


def test_registry_rule_ids_are_unique() -> None:
    registry = InferenceRuleRegistry.default()
    rule_ids = [
        rule.rule_id
        for rule in registry.rules
    ]

    assert len(rule_ids) == len(
        set(rule_ids)
    )
    assert registry.validate() == []


def test_all_v1_rules_are_structural() -> None:
    registry = InferenceRuleRegistry.default()

    assert {
        rule.rule_family
        for rule in registry.rules
    } == {"structural"}


def test_confidence_factors_are_correct() -> None:
    registry = InferenceRuleRegistry.default()

    for rule in registry.rules:
        if rule.rule_type == "transitivity":
            assert rule.confidence_factor == 0.95
        else:
            assert rule.confidence_factor == 1.0


def test_inverse_rule_is_generic() -> None:
    rule = InferenceRule(
        rule_id="inverse-custom",
        name="Inverse custom",
        rule_type="inverse",
        rule_family="structural",
        source_predicate="left_of",
        target_predicate="right_of",
        inverse_predicate="right_of",
        confidence_factor=1.0,
        enabled=True,
    )

    edge = make_edge(
        "edge-1",
        "node-a",
        "left_of",
        "node-b",
    )

    conclusion, bindings, confidence = (
        apply_inverse_rule(rule, edge)
    )

    assert conclusion == (
        "node-b",
        "right_of",
        "node-a",
    )
    assert bindings["target_predicate"] == "right_of"
    assert confidence == 0.9


def test_symmetry_rule_is_generic() -> None:
    rule = InferenceRule(
        rule_id="symmetry-custom",
        name="Symmetry custom",
        rule_type="symmetry",
        rule_family="structural",
        source_predicate="near",
        target_predicate="near",
        inverse_predicate=None,
        confidence_factor=1.0,
        enabled=True,
    )

    edge = make_edge(
        "edge-1",
        "node-a",
        "near",
        "node-b",
    )

    conclusion, bindings, confidence = (
        apply_symmetry_rule(rule, edge)
    )

    assert conclusion == (
        "node-b",
        "near",
        "node-a",
    )
    assert bindings["source_subject_id"] == "node-a"
    assert confidence == 0.9


def test_transitive_rule_is_generic() -> None:
    rule = InferenceRule(
        rule_id="transitivity-custom",
        name="Transitivity custom",
        rule_type="transitivity",
        rule_family="structural",
        source_predicate="before",
        target_predicate="before",
        inverse_predicate=None,
        confidence_factor=0.95,
        enabled=True,
    )

    first = make_edge(
        "edge-1",
        "node-a",
        "before",
        "node-b",
        0.8,
    )

    second = make_edge(
        "edge-2",
        "node-b",
        "before",
        "node-c",
        0.7,
    )

    conclusion, bindings, confidence = (
        apply_transitivity_rule(
            rule,
            first,
            second,
        )
    )

    assert conclusion == (
        "node-a",
        "before",
        "node-c",
    )
    assert bindings["middle_node_id"] == "node-b"
    assert confidence == 0.665


def test_confidence_is_bounded() -> None:
    assert calculate_confidence(
        (2.0,),
        1.0,
    ) == 1.0

    assert calculate_confidence(
        (-1.0,),
        1.0,
    ) == 0.0


def test_rule_module_has_no_v1_predicate_literals() -> None:
    source = inspect.getsource(
        rule_module
    )

    for predicate in (
        "is_a",
        "part_of",
        "contains",
        "equivalent_to",
        "observe",
    ):
        assert predicate not in source
