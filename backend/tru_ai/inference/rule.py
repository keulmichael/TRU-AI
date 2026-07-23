from __future__ import annotations

from tru_ai.graph.models import GraphEdge
from tru_ai.inference.models import (
    EdgeKey,
    InferenceRule,
    canonical_edge_key,
    clamp_confidence,
)


def edge_confidence(
    edge: GraphEdge,
) -> float:
    return clamp_confidence(
        edge.confidence_max
    )


def calculate_confidence(
    premise_confidences: tuple[float, ...],
    confidence_factor: float,
) -> float:
    if not premise_confidences:
        return 0.0

    return round(
        clamp_confidence(
            min(premise_confidences)
            * confidence_factor
        ),
        6,
    )


def apply_inverse_rule(
    rule: InferenceRule,
    edge: GraphEdge,
) -> tuple[EdgeKey, dict[str, str], float]:
    predicate = (
        rule.target_predicate
        or rule.inverse_predicate
    )

    if predicate is None:
        raise ValueError(
            "Une règle inverse doit définir "
            "un prédicat cible."
        )

    conclusion = canonical_edge_key(
        subject_id=edge.object_id,
        predicate=predicate,
        object_id=edge.subject_id,
    )

    bindings = {
        "source_subject_id": edge.subject_id,
        "source_object_id": edge.object_id,
        "target_subject_id": edge.object_id,
        "target_object_id": edge.subject_id,
        "source_predicate": edge.predicate,
        "target_predicate": predicate,
    }

    confidence = calculate_confidence(
        (edge_confidence(edge),),
        rule.confidence_factor,
    )

    return (
        conclusion,
        bindings,
        confidence,
    )


def apply_symmetry_rule(
    rule: InferenceRule,
    edge: GraphEdge,
) -> tuple[EdgeKey, dict[str, str], float]:
    predicate = (
        rule.target_predicate
        or rule.source_predicate
    )

    conclusion = canonical_edge_key(
        subject_id=edge.object_id,
        predicate=predicate,
        object_id=edge.subject_id,
    )

    bindings = {
        "source_subject_id": edge.subject_id,
        "source_object_id": edge.object_id,
        "target_subject_id": edge.object_id,
        "target_object_id": edge.subject_id,
        "source_predicate": edge.predicate,
        "target_predicate": predicate,
    }

    confidence = calculate_confidence(
        (edge_confidence(edge),),
        rule.confidence_factor,
    )

    return (
        conclusion,
        bindings,
        confidence,
    )


def apply_transitivity_rule(
    rule: InferenceRule,
    first_edge: GraphEdge,
    second_edge: GraphEdge,
) -> tuple[EdgeKey, dict[str, str], float]:
    predicate = (
        rule.target_predicate
        or rule.source_predicate
    )

    if first_edge.object_id != second_edge.subject_id:
        raise ValueError(
            "Les prémisses transitives "
            "ne s'unifient pas."
        )

    conclusion = canonical_edge_key(
        subject_id=first_edge.subject_id,
        predicate=predicate,
        object_id=second_edge.object_id,
    )

    bindings = {
        "source_subject_id": first_edge.subject_id,
        "middle_node_id": first_edge.object_id,
        "source_object_id": second_edge.object_id,
        "target_subject_id": first_edge.subject_id,
        "target_object_id": second_edge.object_id,
        "source_predicate": first_edge.predicate,
        "target_predicate": predicate,
    }

    confidence = calculate_confidence(
        (
            edge_confidence(first_edge),
            edge_confidence(second_edge),
        ),
        rule.confidence_factor,
    )

    return (
        conclusion,
        bindings,
        confidence,
    )
