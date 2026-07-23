from tru_ai.semantic.alias_registry import (
    SemanticAliasRegistry,
)


def test_registry_resolves_article_variant():
    registry = SemanticAliasRegistry()

    assert (
        registry.resolve("la conscience")
        == registry.resolve("conscience")
    )


def test_registry_resolves_accent_variant():
    registry = SemanticAliasRegistry()

    assert (
        registry.resolve("la réalité")
        == registry.resolve("realite")
    )


def test_registry_keeps_distinct_concepts_separate():
    registry = SemanticAliasRegistry()

    assert (
        registry.resolve("conscience")
        != registry.resolve("conscience universelle")
    )