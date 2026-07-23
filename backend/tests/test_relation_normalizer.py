from tru_ai.relations.normalizer import (
    RelationNormalizer,
)


def test_entity_normalizer_removes_determiner() -> None:
    normalizer = RelationNormalizer()

    assert normalizer.normalize_entity(
        "La conscience"
    ) == "conscience"


def test_entity_normalizer_removes_accents() -> None:
    normalizer = RelationNormalizer()

    assert normalizer.normalize_entity(
        "La Réflexivité"
    ) == "reflexivite"


def test_predicate_normalizer_uses_infinitive() -> None:
    normalizer = RelationNormalizer()

    assert normalizer.normalize_predicate(
        "transforme"
    ) == "transformer"


def test_predicate_normalizer_handles_capability() -> None:
    normalizer = RelationNormalizer()

    assert normalizer.normalize_predicate(
        "est capable de"
    ) == "etre_capable_de"