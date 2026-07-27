from __future__ import annotations

from tru_ai.memory.builder import CanonicalMemoryBuilder
from tru_ai.memory.models import stable_id
from tru_ai.memory.repository import MemoryRepository


def write_delta_fixture(directory):
    directory.mkdir(exist_ok=True)
    (directory / "traite.md").write_text(
        "\n".join(
            [
                "# Chapitre Delta",
                "",
                "Delta est défini comme l'écart entre l'état prédit et l'état observé.",
                "",
                "Axiome Delta : toute observation transforme la compréhension d'un état.",
                "",
                "Démonstration : si l'observation diffère de la prédiction, donc Delta signale une transformation.",
            ]
        ),
        encoding="utf-8",
    )


def test_canonical_memory_detects_definitions_axioms_and_concepts(tmp_path):
    write_delta_fixture(tmp_path)

    memory, report = CanonicalMemoryBuilder(tmp_path).build()

    assert report.valid is True
    assert report.production_source_count == 1
    assert report.definitions_detected >= 1
    assert report.axioms_detected >= 1
    assert "delta" in {
        concept
        for element in memory.elements
        for concept in element.concept_ids
    }


def test_canonical_memory_serialization_is_deterministic(tmp_path):
    write_delta_fixture(tmp_path)

    first, _ = CanonicalMemoryBuilder(tmp_path).build()
    second, _ = CanonicalMemoryBuilder(tmp_path).build()

    assert first.to_dict() == second.to_dict()


def test_memory_repository_writes_and_loads(tmp_path):
    sources = tmp_path / "sources"
    memory_dir = tmp_path / "memory"
    write_delta_fixture(sources)
    repository = MemoryRepository(sources, memory_dir)

    memory, report = repository.build()
    repository.write(memory, report, {"version": "test"})
    loaded = repository.load()

    assert (memory_dir / "canonical_memory.jsonl").exists()
    assert len(loaded.sources) == len(memory.sources)
    assert len(loaded.elements) == len(memory.elements)


def test_stable_memory_ids_are_reproducible():
    assert stable_id("x", {"b": 2, "a": 1}) == stable_id(
        "x",
        {"a": 1, "b": 2},
    )


def test_semantic_statuses_and_operator_taxonomy_are_recorded(tmp_path):
    write_delta_fixture(tmp_path)

    memory, report = CanonicalMemoryBuilder(tmp_path).build()

    definitions = [
        element
        for element in memory.elements
        if element.element_type == "Définition"
    ]
    operators = [
        element
        for element in memory.elements
        if element.element_type == "Opérateur"
    ]
    assert definitions
    assert definitions[0].semantic_validation_status == "CONFIRMÉ"
    assert report.semantic_precision_estimates
    assert report.confirmed_elements > 0
    assert all(
        element.operator_taxonomy in {None, "operateur_tru_formalise", "operateur_tru_candidat", "processus_theorique", "operation_cognitive_generale"}
        for element in memory.elements
    )
    assert report.executable_operator_count == len(
        [
            element
            for element in operators
            if element.operator_taxonomy == "operateur_tru_formalise"
        ]
    )
