from tru_ai.extraction.concept_lexicon import (
    ConceptLexicon,
)


def test_lexicon_contains_core_concepts() -> None:
    lexicon = ConceptLexicon()

    assert lexicon.get(
        "reconnaissance"
    ) is not None

    assert lexicon.get(
        "reflexivite"
    ) is not None

    assert lexicon.get(
        "conscience"
    ) is not None


def test_lexicon_prioritizes_long_aliases() -> None:
    lexicon = ConceptLexicon()

    aliases = lexicon.aliases_by_length()

    alias_values = [
        alias
        for alias, _ in aliases
    ]

    assert alias_values.index(
        "theorie de la reflexivite universelle"
    ) < alias_values.index(
        "reflexivite"
    )