from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)


def test_normalizer_removes_accents() -> None:
    normalizer = LexicalNormalizer()

    assert normalizer.normalize(
        "Réflexivité Universelle"
    ) == "reflexivite universelle"


def test_normalizer_standardizes_apostrophes() -> None:
    normalizer = LexicalNormalizer()

    assert normalizer.normalize(
        "L’âme reconnaît"
    ) == "l'ame reconnait"


def test_normalizer_preserves_original_mapping() -> None:
    normalizer = LexicalNormalizer()

    value = "La Réflexivité"
    normalized = (
        normalizer.normalize_with_mapping(value)
    )

    assert normalized.text == "la reflexivite"

    start = normalized.text.index(
        "reflexivite"
    )

    end = (
        start + len("reflexivite")
    )

    original_start = (
        normalized.original_indexes[start]
    )

    original_end = (
        normalized.original_indexes[
            end - 1
        ]
        + 1
    )

    assert value[
        original_start:original_end
    ] == "Réflexivité"