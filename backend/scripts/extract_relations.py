from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tru_ai.parsing.models import ParsedSentence
from tru_ai.relations.extractor import (
    RelationExtractor,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "processed"
)

SENTENCES_PATH = (
    PROCESSED_DIRECTORY / "sentences.jsonl"
)

PROPOSITIONS_PATH = (
    PROCESSED_DIRECTORY / "propositions.jsonl"
)

RELATIONS_PATH = (
    PROCESSED_DIRECTORY / "relations.jsonl"
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
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
    extractor = RelationExtractor()

    sentences = read_sentences(
        SENTENCES_PATH
    )

    propositions = []
    relations = []

    for sentence in sentences:
        (
            sentence_propositions,
            sentence_relations,
        ) = extractor.extract(sentence)

        propositions.extend(
            sentence_propositions
        )

        relations.extend(
            sentence_relations
        )

    write_jsonl(
        PROPOSITIONS_PATH,
        [
            proposition.to_dict()
            for proposition in propositions
        ],
    )

    write_jsonl(
        RELATIONS_PATH,
        [
            relation.to_dict()
            for relation in relations
        ],
    )

    predicate_counts = Counter(
        relation.predicate
        for relation in relations
    )

    print()
    print("TRU-AI — Extraction des relations")
    print("---------------------------------")
    print(
        f"Phrases analysées : {len(sentences)}"
    )
    print(
        f"Propositions : {len(propositions)}"
    )
    print(
        f"Relations : {len(relations)}"
    )
    print()
    print(
        f"Propositions : {PROPOSITIONS_PATH}"
    )
    print(
        f"Relations    : {RELATIONS_PATH}"
    )
    print()

    if not relations:
        print(
            "Aucune relation détectée."
        )
        return

    print("Relations détectées :")

    for relation in relations:
        print(
            "- "
            f"{relation.subject_label} "
            f"—[{relation.predicate}]→ "
            f"{relation.object_label}"
        )

    print()
    print("Prédicats :")

    for predicate, count in sorted(
        predicate_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):
        print(f"- {predicate} : {count}")


if __name__ == "__main__":
    main()