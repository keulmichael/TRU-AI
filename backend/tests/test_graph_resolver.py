from tru_ai.graph.resolver import EntityResolver


def test_resolver_maps_known_concept() -> None:
    resolver = EntityResolver()

    node = resolver.resolve(
        "conscience"
    )

    assert node.node_id == (
        "concept-conscience"
    )

    assert node.node_type == "concept"
    assert node.concept_id == "conscience"


def test_resolver_is_accent_insensitive() -> None:
    resolver = EntityResolver()

    node = resolver.resolve(
        "Réflexivité"
    )

    assert node.node_id == (
        "concept-reflexivite"
    )

    assert node.node_type == "concept"


def test_resolver_creates_generic_entity() -> None:
    resolver = EntityResolver()

    node = resolver.resolve(
        "approche scientifique"
    )

    assert node.node_id.startswith(
        "entity-"
    )

    assert node.node_type == "entity"
    assert node.concept_id is None


def test_resolver_ids_are_deterministic() -> None:
    resolver = EntityResolver()

    first = resolver.resolve(
        "approche scientifique"
    )

    second = resolver.resolve(
        "Approche scientifique"
    )

    assert first.node_id == second.node_id