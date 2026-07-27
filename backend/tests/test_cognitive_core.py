from __future__ import annotations

from tru_ai.cognitive.core import CognitiveCore
from tru_ai.memory.builder import CanonicalMemoryBuilder


def build_memory(tmp_path):
    (tmp_path / "traite.md").write_text(
        "\n".join(
            [
                "# Chapitre Delta",
                "",
                "Delta est défini comme l'écart entre l'état prédit et l'état observé.",
                "",
                "Axiome Delta : toute observation transforme la compréhension d'un état.",
                "",
                "La TRU relie reconnaissance, observation et transformation.",
                "",
                "La reconnaissance relie observation et transformation.",
            ]
        ),
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()
    return memory


def test_cognitive_core_explains_delta_with_explicit_claim(tmp_path):
    core = CognitiveCore(build_memory(tmp_path))

    response = core.ask("Explique-moi Delta.")

    assert response.trace.intent == "concept_explanation"
    assert "delta" in response.trace.selected_concepts
    assert response.classifications["EXPLICITE"]
    assert response.trace.definitions_used
    assert response.confidence > 0


def test_cognitive_core_preserves_sources_pages_and_evidence(tmp_path):
    response = CognitiveCore(build_memory(tmp_path)).ask("Qu'est-ce que Delta ?")

    assert response.sources
    assert response.evidence
    assert all(evidence.element_id for evidence in response.evidence)


def test_cognitive_core_is_honest_when_evidence_is_missing(tmp_path):
    (tmp_path / "traite.md").write_text("# Vide\n\nLa TRU existe.", encoding="utf-8")
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.classifications["INCONNU"]
    assert response.missing_knowledge
    assert response.confidence == 0.0


def test_cognitive_core_burnout_analysis_is_not_medical_diagnosis(tmp_path):
    core = CognitiveCore(build_memory(tmp_path))

    response = core.ask("Analyse le burn-out selon la TRU.")

    assert response.trace.intent == "applied_analysis"
    assert response.classifications["HYPOTHÈSE"]
    assert any("diagnostic médical" in warning for warning in response.warnings)


def test_cognitive_core_response_is_deterministic(tmp_path):
    core = CognitiveCore(build_memory(tmp_path))

    first = core.ask("Explique-moi Delta.").to_dict()
    second = core.ask("Explique-moi Delta.").to_dict()

    assert first == second
