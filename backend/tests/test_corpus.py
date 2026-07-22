from pathlib import Path

import pytest

from tru_ai.extraction.corpus import CorpusManager


def test_corpus_manager_loads_markdown_documents(
    tmp_path: Path,
) -> None:
    source = tmp_path / "001-introduction.md"

    source.write_text(
        "# Introduction\n\n"
        "La reconnaissance constitue un processus réflexif.",
        encoding="utf-8",
    )

    manager = CorpusManager(tmp_path)
    documents = manager.load()

    assert len(documents) == 1

    document = documents[0]

    assert document.title == "Introduction"
    assert document.source_path == "001-introduction.md"
    assert document.word_count > 0
    assert len(document.content_hash) == 64
    assert document.document_id.startswith("001-introduction-")


def test_corpus_manager_creates_chunks(
    tmp_path: Path,
) -> None:
    source = tmp_path / "document.md"

    source.write_text(
        "# Document\n\n"
        + " ".join(f"mot{i}" for i in range(30)),
        encoding="utf-8",
    )

    manager = CorpusManager(
        tmp_path,
        chunk_size=10,
        chunk_overlap=2,
    )

    documents = manager.load()
    chunks = manager.build_chunks(documents)

    assert len(chunks) >= 3
    assert chunks[0].position == 0
    assert chunks[0].document_id == documents[0].document_id
    assert chunks[0].word_count == 10


def test_invalid_chunk_configuration(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        CorpusManager(
            tmp_path,
            chunk_size=100,
            chunk_overlap=100,
        )