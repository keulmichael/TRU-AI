from tru_ai.extraction.concept_extractor import (
    ConceptExtractor,
)
from tru_ai.parsing.models import ParsedSentence


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


def test_extractor_detects_core_concepts() -> None:
    sentence = make_sentence(
        "La conscience observe la réalité "
        "et permet la reconnaissance."
    )

    extractor = ConceptExtractor()

    occurrences = extractor.extract(
        sentence
    )

    concept_ids = {
        occurrence.concept_id
        for occurrence in occurrences
    }

    assert "conscience" in concept_ids
    assert "observation" in concept_ids
    assert "realite" in concept_ids
    assert "reconnaissance" in concept_ids


def test_extractor_is_accent_insensitive() -> None:
    sentence = make_sentence(
        "La reflexivite produit une "
        "reconnaissance."
    )

    extractor = ConceptExtractor()

    occurrences = extractor.extract(
        sentence
    )

    concept_ids = {
        occurrence.concept_id
        for occurrence in occurrences
    }

    assert "reflexivite" in concept_ids
    assert "reconnaissance" in concept_ids


def test_extractor_preserves_matched_text() -> None:
    sentence = make_sentence(
        "La Réflexivité transforme "
        "la relation."
    )

    extractor = ConceptExtractor()

    occurrences = extractor.extract(
        sentence
    )

    reflexivity = next(
        occurrence
        for occurrence in occurrences
        if occurrence.concept_id
        == "reflexivite"
    )

    assert (
        reflexivity.matched_text
        == "Réflexivité"
    )


def test_extractor_avoids_nested_matches() -> None:
    sentence = make_sentence(
        "La Théorie de la Réflexivité "
        "Universelle propose un cadre."
    )

    extractor = ConceptExtractor()

    occurrences = extractor.extract(
        sentence
    )

    concept_ids = [
        occurrence.concept_id
        for occurrence in occurrences
    ]

    assert "tru" in concept_ids
    assert "reflexivite" not in concept_ids