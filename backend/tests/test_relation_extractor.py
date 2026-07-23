from tru_ai.parsing.models import ParsedSentence
from tru_ai.relations.extractor import (
    RelationExtractor,
)


def make_sentence(
    content: str,
) -> ParsedSentence:
    return ParsedSentence(
        sentence_id="sentence-001",
        document_id="document-001",
        section_id="section-001",
        paragraph_id="paragraph-001",
        position=0,
        content=content,
        word_count=len(content.split()),
    )


def test_extracts_transitive_relation() -> None:
    sentence = make_sentence(
        "La reconnaissance transforme "
        "la conscience."
    )

    extractor = RelationExtractor()

    propositions, relations = (
        extractor.extract(sentence)
    )

    assert len(propositions) == 1
    assert len(relations) == 1

    relation = relations[0]

    assert (
        relation.subject_label
        == "reconnaissance"
    )
    assert relation.predicate == "transformer"
    assert relation.object_label == "conscience"


def test_extracts_capability_relation() -> None:
    sentence = make_sentence(
        "Toute conscience est capable "
        "d'observer."
    )

    extractor = RelationExtractor()

    _, relations = extractor.extract(
        sentence
    )

    assert len(relations) == 1

    relation = relations[0]

    assert relation.subject_label == "conscience"
    assert (
        relation.predicate
        == "etre_capable_de"
    )
    assert relation.object_label == "observer"


def test_extracts_tru_proposition() -> None:
    sentence = make_sentence(
        "La Théorie de la Réflexivité "
        "Universelle propose une approche "
        "scientifique de la reconnaissance."
    )

    extractor = RelationExtractor()

    _, relations = extractor.extract(
        sentence
    )

    assert len(relations) == 1

    relation = relations[0]

    assert relation.subject_label == (
        "theorie de la reflexivite universelle"
    )

    assert relation.predicate == "proposer"

    assert relation.object_label == (
        "approche scientifique "
        "de la reconnaissance"
    )


def test_returns_no_relation_for_unknown_form() -> None:
    sentence = make_sentence(
        "Une phrase sans structure reconnue."
    )

    extractor = RelationExtractor()

    propositions, relations = (
        extractor.extract(sentence)
    )

    assert propositions == []
    assert relations == []


def test_relation_ids_are_deterministic() -> None:
    sentence = make_sentence(
        "La conscience observe la réalité."
    )

    extractor = RelationExtractor()

    _, first_relations = extractor.extract(
        sentence
    )

    _, second_relations = extractor.extract(
        sentence
    )

    assert (
        first_relations[0].relation_id
        == second_relations[0].relation_id
    )


def test_splits_semicolon_clauses() -> None:
    sentence = make_sentence(
        "La conscience observe la réalité ; "
        "la reconnaissance transforme "
        "la conscience."
    )

    extractor = RelationExtractor()

    _, relations = extractor.extract(
        sentence
    )

    assert len(relations) == 2

    predicates = {
        relation.predicate
        for relation in relations
    }

    assert predicates == {
        "observer",
        "transformer",
    }