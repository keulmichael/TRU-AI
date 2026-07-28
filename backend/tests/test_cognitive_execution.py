from __future__ import annotations

from tru_ai.cognitive.core import CognitiveCore
from tru_ai.memory.builder import CanonicalMemoryBuilder


def build_delta_memory(tmp_path):
    (tmp_path / "traite.md").write_text(
        "\n".join(
            [
                "# Chapitre Delta",
                "",
                "Delta désigne l'écart entre l'état actuel et la possibilité reconnue.",
                "",
                "Axiome Delta : une conscience compare un état observé avec une transformation possible.",
                "",
                "Cette proposition relie observation, reconnaissance et transformation.",
            ]
        ),
        encoding="utf-8",
    )
    memory, report = CanonicalMemoryBuilder(tmp_path).build()
    assert report.valid
    return memory


def test_execution_builds_problem_and_formalizes_delta(tmp_path):
    response = CognitiveCore(build_delta_memory(tmp_path)).ask(
        "Explique-moi Delta."
    )

    execution = response.execution
    assert execution is not None
    assert execution.problem
    assert "delta" in execution.concepts_recognized
    assert execution.comparisons
    assert execution.applicable_operators
    assert execution.applied_operators[0].applied is False
    assert not response.classifications["DÉDUCTION"]


def test_delta_applies_only_with_two_explicit_states(tmp_path):
    response = CognitiveCore(build_delta_memory(tmp_path)).ask(
        "Applique Delta à cette situation : l'état actuel est fatigue chronique et l'état reconnu comme possible est récupération."
    )

    execution = response.execution
    assert execution is not None
    assert execution.applied_operators[0].applied is True
    assert response.classifications["DÉDUCTION"]


def test_delta_refuses_without_formalized_operator(tmp_path):
    (tmp_path / "traite.md").write_text(
        "# Observation\n\nLa reconnaissance observe une transformation.",
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.execution is not None
    assert response.execution.applied_operators[0].applied is False
    assert response.missing_knowledge


def test_comparison_describes_states_and_limitations(tmp_path):
    response = CognitiveCore(build_delta_memory(tmp_path)).ask(
        "Analyse le burn-out selon la TRU."
    )

    comparison = response.execution.comparisons[0]
    assert comparison.compared_states
    assert comparison.dimensions
    assert response.classifications["HYPOTHÈSE"]
    assert response.warnings


def test_contradiction_is_detected(tmp_path):
    (tmp_path / "traite.md").write_text(
        "\n".join(
            [
                "# Delta",
                "",
                "Delta désigne l'écart entre deux états.",
                "",
                "Delta n'est pas une mesure d'écart entre deux états.",
            ]
        ),
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.execution.contradictions
    assert response.execution.reflexive_evaluation["contradiction_detected"]


def test_operator_formalization_contains_required_fields(tmp_path):
    response = CognitiveCore(build_delta_memory(tmp_path)).ask(
        "Explique-moi Delta."
    )

    operator = response.execution.applicable_operators[0]
    assert operator.operator_id
    assert operator.definitions
    assert operator.inputs
    assert operator.preconditions
    assert operator.outputs
    assert operator.source_evidence


def test_execution_is_deterministic(tmp_path):
    core = CognitiveCore(build_delta_memory(tmp_path))

    first = core.ask("Explique-moi Delta.").execution.to_dict()
    second = core.ask("Explique-moi Delta.").execution.to_dict()

    assert first == second
