from __future__ import annotations

from dataclasses import dataclass

from tru_ai.inference.models import (
    InferenceRule,
)


VALID_RULE_TYPES = {
    "transitivity",
    "inverse",
    "symmetry",
}

VALID_RULE_FAMILIES = {
    "structural",
    "semantic",
    "temporal",
    "causal",
    "tru",
}


def build_default_rules() -> tuple[InferenceRule, ...]:
    rules: list[InferenceRule] = []

    for predicate in (
        "is_a",
        "part_of",
        "depends_on",
        "implies",
    ):
        rules.append(
            InferenceRule(
                rule_id=(
                    f"transitivity-{predicate}"
                ),
                name=(
                    f"Transitivity of {predicate}"
                ),
                rule_type="transitivity",
                rule_family="structural",
                source_predicate=predicate,
                target_predicate=predicate,
                inverse_predicate=None,
                confidence_factor=0.95,
                enabled=True,
            )
        )

    inverse_pairs = (
        ("contains", "part_of"),
        ("causes", "caused_by"),
        ("precedes", "follows"),
        ("includes", "included_in"),
    )

    for source, target in inverse_pairs:
        rules.append(
            InferenceRule(
                rule_id=(
                    f"inverse-{source}-to-{target}"
                ),
                name=(
                    f"Inverse of {source} as {target}"
                ),
                rule_type="inverse",
                rule_family="structural",
                source_predicate=source,
                target_predicate=target,
                inverse_predicate=target,
                confidence_factor=1.0,
                enabled=True,
            )
        )

        rules.append(
            InferenceRule(
                rule_id=(
                    f"inverse-{target}-to-{source}"
                ),
                name=(
                    f"Inverse of {target} as {source}"
                ),
                rule_type="inverse",
                rule_family="structural",
                source_predicate=target,
                target_predicate=source,
                inverse_predicate=source,
                confidence_factor=1.0,
                enabled=True,
            )
        )

    for predicate in (
        "equivalent_to",
        "related_to",
        "interacts_with",
    ):
        rules.append(
            InferenceRule(
                rule_id=(
                    f"symmetry-{predicate}"
                ),
                name=(
                    f"Symmetry of {predicate}"
                ),
                rule_type="symmetry",
                rule_family="structural",
                source_predicate=predicate,
                target_predicate=predicate,
                inverse_predicate=None,
                confidence_factor=1.0,
                enabled=True,
            )
        )

    return tuple(rules)


@dataclass(frozen=True)
class InferenceRuleRegistry:
    rules: tuple[InferenceRule, ...]

    @classmethod
    def default(cls) -> InferenceRuleRegistry:
        return cls(
            rules=build_default_rules()
        )

    def active_rules(
        self,
    ) -> tuple[InferenceRule, ...]:
        return tuple(
            rule
            for rule in self.rules
            if rule.enabled
        )

    def get(
        self,
        rule_id: str,
    ) -> InferenceRule | None:
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule

        return None

    def validate(
        self,
    ) -> list[str]:
        errors: list[str] = []
        seen_rule_ids: set[str] = set()

        for rule in self.rules:
            if rule.rule_id in seen_rule_ids:
                errors.append(
                    "Règle dupliquée : "
                    f"{rule.rule_id}"
                )

            seen_rule_ids.add(
                rule.rule_id
            )

            if rule.rule_type not in VALID_RULE_TYPES:
                errors.append(
                    "Type de règle invalide : "
                    f"{rule.rule_id}"
                )

            if (
                rule.rule_family
                not in VALID_RULE_FAMILIES
            ):
                errors.append(
                    "Famille de règle invalide : "
                    f"{rule.rule_id}"
                )

            if not (
                0.0
                <= rule.confidence_factor
                <= 1.0
            ):
                errors.append(
                    "Facteur de confiance invalide : "
                    f"{rule.rule_id}"
                )

            if not rule.source_predicate:
                errors.append(
                    "Prédicat source absent : "
                    f"{rule.rule_id}"
                )

            if (
                rule.rule_type == "inverse"
                and not (
                    rule.target_predicate
                    or rule.inverse_predicate
                )
            ):
                errors.append(
                    "Prédicat inverse absent : "
                    f"{rule.rule_id}"
                )

            if (
                rule.rule_type
                in {
                    "transitivity",
                    "symmetry",
                }
                and not rule.target_predicate
            ):
                errors.append(
                    "Prédicat cible absent : "
                    f"{rule.rule_id}"
                )

        return errors
