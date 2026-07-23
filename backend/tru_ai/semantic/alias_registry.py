from __future__ import annotations

from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)


DEFAULT_ALIASES: dict[str, set[str]] = {
    "conscience": {
        "la conscience",
    },
    "realite": {
        "la réalité",
        "la realite",
    },
    "observation": {
        "l'observation",
        "l’observation",
    },
    "reconnaissance": {
        "la reconnaissance",
    },
    "temps": {
        "le temps",
    },
    "memoire": {
        "la mémoire",
        "la memoire",
    },
}


class SemanticAliasRegistry:
    def __init__(
        self,
        aliases: dict[str, set[str]] | None = None,
        normalizer: LexicalNormalizer | None = None,
    ) -> None:
        self.normalizer = (
            normalizer or LexicalNormalizer()
        )

        self.alias_to_canonical: dict[
            str,
            str,
        ] = {}

        source = aliases or DEFAULT_ALIASES

        for canonical, variants in source.items():
            normalized_canonical = (
                self.normalizer.normalize(
                    canonical
                )
            )

            self.alias_to_canonical[
                normalized_canonical
            ] = normalized_canonical

            for variant in variants:
                normalized_variant = (
                    self.normalizer.normalize(
                        variant
                    )
                )

                self.alias_to_canonical[
                    normalized_variant
                ] = normalized_canonical

    def resolve(
        self,
        value: str,
    ) -> str:
        normalized = self.normalizer.normalize(
            value
        )

        return self.alias_to_canonical.get(
            normalized,
            normalized,
        )

    def are_equivalent(
        self,
        first: str,
        second: str,
    ) -> bool:
        return (
            self.resolve(first)
            == self.resolve(second)
        )