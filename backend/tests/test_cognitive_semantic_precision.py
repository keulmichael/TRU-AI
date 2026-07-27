from __future__ import annotations

import json
from pathlib import Path

from tru_ai.cognitive.core import CognitiveCore
from tru_ai.memory.builder import CanonicalMemoryBuilder


REFERENCE_CASES = Path(__file__).resolve().parents[2] / "corpus" / "validation" / "semantic_reference_cases.json"


def build_reference_memory(tmp_path):
    cases = json.loads(REFERENCE_CASES.read_text(encoding="utf-8"))
    lines = ["# Corpus de validation sémantique", ""]
    for case in cases:
        if case["expected_classification"] in {
            "Définition",
            "Axiome",
            "Proposition",
            "Démonstration",
            "Observation",
            "Exemple",
            "Hypothèse",
            "Opérateur",
            "Paragraphe",
        }:
            lines.extend([case["text"], ""])
    (tmp_path / "semantic.md").write_text("\n".join(lines), encoding="utf-8")
    memory, report = CanonicalMemoryBuilder(tmp_path).build()
    assert report.valid
    return memory, report


def test_semantic_reference_corpus_has_at_least_thirty_cases():
    cases = json.loads(REFERENCE_CASES.read_text(encoding="utf-8"))

    assert len(cases) >= 30
    assert all(case["case_id"] and case["justification"] for case in cases)


def test_operator_taxonomy_restricts_executable_operators(tmp_path):
    memory, report = build_reference_memory(tmp_path)

    executable = [
        element
        for element in memory.elements
        if element.operator_taxonomy == "operateur_tru_formalise"
    ]
    candidates = [
        element
        for element in memory.elements
        if element.operator_taxonomy == "operateur_tru_candidat"
    ]

    assert executable
    assert all("Delta" in element.text for element in executable)
    assert report.executable_operator_count == len(executable)
    assert report.candidate_operator_count == len(candidates)


def test_explain_delta_does_not_apply_delta_without_two_states(tmp_path):
    memory, _ = build_reference_memory(tmp_path)

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.execution is not None
    assert response.execution.applicable_operators
    assert response.execution.applied_operators[0].applied is False
    assert response.classifications["EXPLICITE"]
    assert not response.classifications["DÉDUCTION"]


def test_apply_delta_requires_two_comparable_states(tmp_path):
    memory, _ = build_reference_memory(tmp_path)

    response = CognitiveCore(memory).ask(
        "Applique Delta à cette situation : l'état actuel est épuisement et l'état reconnu comme possible est récupération."
    )

    assert response.execution is not None
    application = response.execution.applied_operators[0]
    assert application.applied is True
    assert application.rule == "delta_compares_current_state_with_recognized_possibility"
    deduction = response.classifications["DÉDUCTION"][0]
    assert deduction["premises"]
    assert deduction["rule"] == application.rule
    assert deduction["validity_score"] == application.confidence


def test_structured_contradiction_requires_same_property(tmp_path):
    (tmp_path / "semantic.md").write_text(
        "\n".join(
            [
                "# Delta",
                "",
                "Delta mesure l'écart entre deux états.",
                "",
                "Delta n'est pas une mesure d'écart entre deux états.",
            ]
        ),
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.execution is not None
    assert response.execution.contradictions


def test_delta_formulations_are_not_lexical_contradictions(tmp_path):
    (tmp_path / "semantic.md").write_text(
        "\n".join(
            [
                "# Delta",
                "",
                "Delta désigne l'écart entre la configuration présente et la configuration devenue concevable.",
                "",
                "Delta désigne la distance vivante entre ce qui est et ce qui est représenté.",
            ]
        ),
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.execution is not None
    assert response.execution.contradictions == ()


def test_delta_quantitative_limitation_is_not_a_contradiction(tmp_path):
    (tmp_path / "semantic.md").write_text(
        "\n".join(
            [
                "# Delta",
                "",
                "Un second Delta peut être défini entre affectation et réalité : ΔAR=An−Rn.",
                "",
                "Cette notation ne mesure pas une erreur quantitative, mais désigne l'écart possible entre deux représentations.",
            ]
        ),
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Quelle est la définition exacte de Delta ?")

    assert response.execution is not None
    assert response.execution.contradictions == ()


def test_delta_interpretation_limit_is_not_a_contradiction(tmp_path):
    (tmp_path / "semantic.md").write_text(
        "\n".join(
            [
                "# Delta",
                "",
                "Delta désigne l'écart entre deux états.",
                "",
                "Delta ne doit donc pas être conçu comme un défaut universel.",
            ]
        ),
        encoding="utf-8",
    )
    memory, _ = CanonicalMemoryBuilder(tmp_path).build()

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.execution is not None
    assert response.execution.contradictions == ()


def test_confidence_is_decomposed(tmp_path):
    memory, _ = build_reference_memory(tmp_path)

    response = CognitiveCore(memory).ask("Explique-moi Delta.")

    assert response.confidence_breakdown["source_coverage"] > 0
    assert response.confidence_breakdown["evidence_quality"] > 0
    assert response.confidence_breakdown["final_confidence"] == response.confidence


def test_burnout_analysis_marks_hypothesis_and_no_medical_diagnosis(tmp_path):
    memory, _ = build_reference_memory(tmp_path)

    response = CognitiveCore(memory).ask("Analyse le burn-out selon la TRU.")

    assert response.classifications["HYPOTHÈSE"]
    assert response.execution is not None
    assert response.execution.applied_operators[0].applied is False
    assert any("diagnostic médical" in warning for warning in response.warnings)
