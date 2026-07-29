from tru_ai.cognitive.reasoning import (
    ReasoningExecutor, ReasoningPlanner, ReasoningRequest, VerificationStatus,
)


def execute(observations):
    plan = ReasoningPlanner().plan(ReasoningRequest(question="Teste cette prédiction.", intent="scientific_research"))
    return ReasoningExecutor().execute(plan, conversation_context={
        "theory": {"id": "tru", "claims": [{"id": "c1", "text": "La répétition stabilise la relation.", "status": "supported"}]},
        "predictions": [{
            "id": "p1", "text": "La stabilité augmente.", "source_claim_ids": ["c1"],
            "falsification_condition": "La stabilité diminue malgré la répétition.",
            "expected_observation": "Hausse de la stabilité.",
        }],
        "scientific_observations": observations,
    })


def test_v94_confirms_compatible_prediction():
    result = execute([{"id": "o1", "prediction_id": "p1", "text": "Hausse observée", "compatibility_score": 0.9}])
    assert result.verification_reports[0].status is VerificationStatus.CONFIRMED
    assert result.falsification_reports[0].falsified is False
    assert result.scientific_theory_revisions[0].action == "retain"


def test_v94_formally_falsifies_prediction():
    result = execute([{"id": "o1", "prediction_id": "p1", "text": "Baisse observée", "compatibility_score": 0.1, "matches_falsification_condition": True}])
    report = result.falsification_reports[0]
    assert report.formal_test_possible is True
    assert report.falsification_condition_met is True
    assert report.falsified is True
    assert report.revision_required is True
    assert result.scientific_theory_revisions[0].action == "revise"


def test_v94_does_not_claim_falsification_without_condition():
    result = execute([{"id": "o1", "prediction_id": "p1", "text": "Observation ambiguë"}])
    assert result.verification_reports[0].status is VerificationStatus.INCONCLUSIVE
    assert result.falsification_reports[0].falsified is False


def test_v94_unlinked_prediction_remains_untested():
    result = execute([])
    assert result.verification_reports[0].status is VerificationStatus.UNTESTED
    assert result.verification_reports[0].evidence_score == 0.0


def test_v94_serializes_reports_and_operator_trace():
    result = execute([{"id": "o1", "prediction_id": "p1", "text": "Hausse", "supports_prediction": True}])
    payload = result.to_dict()
    assert payload["scientific_observations"][0]["observation_id"] == "o1"
    assert payload["verification_reports"][0]["status"] == "confirmed"
    assert payload["falsification_reports"][0]["prediction_id"] == "p1"
    operators = [item["operator"] for item in payload["operator_trace"]]
    assert "VerificationOperator" in operators
    assert "FalsificationOperator" in operators
