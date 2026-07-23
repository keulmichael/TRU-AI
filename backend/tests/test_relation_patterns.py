from tru_ai.relations.patterns import (
    RELATION_PATTERNS,
)


def test_patterns_have_unique_ids() -> None:
    pattern_ids = [
        pattern.pattern_id
        for pattern in RELATION_PATTERNS
    ]

    assert len(pattern_ids) == len(
        set(pattern_ids)
    )


def test_capability_pattern_matches() -> None:
    pattern = next(
        pattern
        for pattern in RELATION_PATTERNS
        if pattern.pattern_id == "capable_de"
    )

    match = pattern.expression.match(
        "Toute conscience est capable "
        "d'observer."
    )

    assert match is not None
    assert (
        match.group("subject")
        == "Toute conscience"
    )
    assert (
        match.group("object")
        == "observer"
    )


def test_transitive_pattern_matches() -> None:
    pattern = next(
        pattern
        for pattern in RELATION_PATTERNS
        if pattern.pattern_id
        == "transitive_verb"
    )

    match = pattern.expression.match(
        "La reconnaissance transforme "
        "la conscience."
    )

    assert match is not None
    assert (
        match.group("predicate")
        == "transforme"
    )