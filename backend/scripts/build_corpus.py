from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from tru_ai.extraction.corpus import CorpusManager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CORPUS_DIRECTORY = PROJECT_ROOT / "corpus" / "raw"
PROCESSED_CORPUS_DIRECTORY = PROJECT_ROOT / "corpus" / "processed"


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def main() -> None:
    PROCESSED_CORPUS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    manager = CorpusManager(
        corpus_directory=RAW_CORPUS_DIRECTORY,
        chunk_size=250,
        chunk_overlap=40,
    )

    documents = manager.load()
    chunks = manager.build_chunks(documents)

    document_records = [
        manager.document_to_dict(document)
        for document in documents
    ]

    chunk_records = [
        manager.chunk_to_dict(chunk)
        for chunk in chunks
    ]

    documents_path = (
        PROCESSED_CORPUS_DIRECTORY / "documents.jsonl"
    )

    chunks_path = (
        PROCESSED_CORPUS_DIRECTORY / "chunks.jsonl"
    )

    manifest_path = (
        PROCESSED_CORPUS_DIRECTORY / "manifest.json"
    )

    write_jsonl(documents_path, document_records)
    write_jsonl(chunks_path, chunk_records)

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_directory": str(RAW_CORPUS_DIRECTORY),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "total_word_count": sum(
            document.word_count for document in documents
        ),
        "chunk_size": manager.chunk_size,
        "chunk_overlap": manager.chunk_overlap,
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("TRU-AI — Construction du corpus")
    print("--------------------------------")
    print(f"Documents : {len(documents)}")
    print(f"Fragments : {len(chunks)}")
    print(
        "Nombre total de mots : "
        f"{manifest['total_word_count']}"
    )
    print()
    print(f"Documents : {documents_path}")
    print(f"Fragments : {chunks_path}")
    print(f"Manifest  : {manifest_path}")
    print()

    for document in documents:
        print(
            f"- {document.document_id} | "
            f"{document.title} | "
            f"{document.word_count} mots"
        )


if __name__ == "__main__":
    main()