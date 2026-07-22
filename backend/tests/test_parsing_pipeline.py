from pathlib import Path

from tru_ai.extraction.corpus import CorpusManager
from tru_ai.parsing.pipeline import ParsingPipeline


def test_pipeline_processes_document(
    tmp_path: Path,
) -> None:
    source = tmp_path / "document.md"

    source.write_text(
        "# Introduction\n\n"
        "La conscience observe. "
        "Elle reconnaît une transformation.\n\n"
        "Le processus devient réflexif.",
        encoding="utf-8",
    )

    manager = CorpusManager(tmp_path)
    documents = manager.load()

    pipeline = ParsingPipeline()
    result = pipeline.process(documents)

    assert len(result.sections) == 1
    assert len(result.paragraphs) == 2
    assert len(result.sentences) == 3

    assert result.sentences[0].content == (
        "La conscience observe."
    )