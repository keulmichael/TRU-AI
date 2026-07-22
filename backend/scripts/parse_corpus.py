from __future__ import annotations

import json
from pathlib import Path

from tru_ai.extraction.corpus import CorpusManager
from tru_ai.parsing.pipeline import ParsingPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_CORPUS_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "raw"
)

PROCESSED_CORPUS_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "processed"
)


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
    PROCESSED_CORPUS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    corpus_manager = CorpusManager(
        RAW_CORPUS_DIRECTORY
    )

    documents = corpus_manager.load()

    pipeline = ParsingPipeline()
    result = pipeline.process(documents)

    sections_path = (
        PROCESSED_CORPUS_DIRECTORY
        / "sections.jsonl"
    )

    paragraphs_path = (
        PROCESSED_CORPUS_DIRECTORY
        / "paragraphs.jsonl"
    )

    sentences_path = (
        PROCESSED_CORPUS_DIRECTORY
        / "sentences.jsonl"
    )

    write_jsonl(
        sections_path,
        [
            section.to_dict()
            for section in result.sections
        ],
    )

    write_jsonl(
        paragraphs_path,
        [
            paragraph.to_dict()
            for paragraph in result.paragraphs
        ],
    )

    write_jsonl(
        sentences_path,
        [
            sentence.to_dict()
            for sentence in result.sentences
        ],
    )

    print()
    print("TRU-AI — Analyse linguistique")
    print("--------------------------------")
    print(f"Documents  : {len(documents)}")
    print(f"Sections   : {len(result.sections)}")
    print(f"Paragraphes: {len(result.paragraphs)}")
    print(f"Phrases    : {len(result.sentences)}")
    print()
    print(f"Sections   : {sections_path}")
    print(f"Paragraphes: {paragraphs_path}")
    print(f"Phrases    : {sentences_path}")
    print()

    for sentence in result.sentences:
        print(
            f"- {sentence.sentence_id}: "
            f"{sentence.content}"
        )


if __name__ == "__main__":
    main()