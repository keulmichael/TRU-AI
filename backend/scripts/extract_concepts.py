from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tru_ai.extraction.concept_extractor import (
    ConceptExtractor,
)
from tru_ai.extraction.concept_lexicon import (
    ConceptLexicon,
)
from tru_ai.parsing.models import ParsedSentence


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_CORPUS_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "processed"
)

SENTENCES_PATH = (
    PROCESSED_CORPUS_DIRECTORY
    / "sentences.jsonl"
)

CONCEPTS_PATH = (
    PROCESSED_CORPUS_DIRECTORY
    / "concepts.jsonl"
)

OCCURRENCES_PATH = (
    PROCESSED_CORPUS_DIRECTORY
    / "concept_occurrences.jsonl"
)


def read_sentences(
    path: Path,
) -> list[ParsedSentence]:
    if not path.exists():
        raise FileNotFoundError(
            "Le fichier sentences.jsonl est absent. "
            "Exécute d'abord : "
            "python scripts\\parse_corpus.py"
        )

    sentences: list[ParsedSentence] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as input_file:
        for line_number, line in enumerate(
            input_file,
            start=1,
        ):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
                sentences.append(
                    ParsedSentence(**record)
                )
            except (
                json.JSONDecodeError,
                TypeError,
            ) as error:
                raise ValueError(
                    "Phrase invalide à la ligne "
                    f"{line_number} de {path}."
                ) from error

    return sentences


def write_jsonl(
    path: Path,
    records: list[dict],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for record in records:
            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> None:
    lexicon = ConceptLexicon()
    extractor = ConceptExtractor(
        lexicon=lexicon
    )

    sentences = read_sentences(
        SENTENCES_PATH
    )

    occurrences = []

    for sentence in sentences:
        occurrences.extend(
            extractor.extract(sentence)
        )

    concepts = lexicon.all_concepts()

    write_jsonl(
        CONCEPTS_PATH,
        [
            concept.to_dict()
            for concept in concepts
        ],
    )

    write_jsonl(
        OCCURRENCES_PATH,
        [
            occurrence.to_dict()
            for occurrence in occurrences
        ],
    )

    concept_counts = Counter(
        occurrence.concept_id
        for occurrence in occurrences
    )

    print()
    print("TRU-AI — Extraction des concepts")
    print("--------------------------------")
    print(f"Phrases analysées : {len(sentences)}")
    print(f"Concepts du lexique : {len(concepts)}")
    print(
        "Occurrences détectées : "
        f"{len(occurrences)}"
    )
    print()
    print(f"Concepts    : {CONCEPTS_PATH}")
    print(f"Occurrences : {OCCURRENCES_PATH}")
    print()

    if not occurrences:
        print(
            "Aucune occurrence de concept détectée."
        )
        return

    print("Concepts détectés :")

    for concept_id, count in sorted(
        concept_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):
        concept = lexicon.get(concept_id)

        label = (
            concept.preferred_label
            if concept is not None
            else concept_id
        )

        print(f"- {label} : {count}")


if __name__ == "__main__":
    main()