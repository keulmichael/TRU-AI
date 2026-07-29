from tru_ai.cognitive.reasoning import (
    PredictionConfidenceLevel,
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
)


def execute(context: dict):
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Produis une prédiction scientifique.", intent="scientific_research")
    )
    return ReasoningExecutor().execute(plan, conversation_context=context)


def theory_context() -> dict:
    return {
        "theory": {
            "id": "tru",
            "claims": [{
                "id": "c1",
                "text": "La reconnaissance répétée stabilise une relation.",
                "status": "supported",
                "evidence": ["observation-a", "observation-b"],
            }],
        },
        "predictions": [{
            "id": "p1",
            "text": "Une reconnaissance répétée augmentera la stabilité observée.",
            "source_claim_ids": ["c1"],
            "falsification_condition": "La stabilité ne progresse pas malgré la répétition.",
            "expected_observation": "Une hausse mesurable de la stabilité.",
            "horizon": "trois cycles",
            "assumptions": ["la répétition est maintenue"],
        }],
    }


def test_v93_computes_prediction_confidence() -> None:
    result = execute(theory_context())
    prediction = result.scientific_predictions[0]
    assert 0.0 <= prediction.confidence <= 1.0
    assert prediction.confidence_level in {
        PredictionConfidenceLevel.MODERATE,
        PredictionConfidenceLevel.HIGH,
        PredictionConfidenceLevel.VERY_HIGH,
    }
    assert prediction.confidence_factors
    assert prediction.expected_observation == "Une hausse mesurable de la stabilité."


def test_v93_preserves_explicit_confidence() -> None:
    context = theory_context()
    context["predictions"][0]["confidence"] = 0.91
    prediction = execute(context).scientific_predictions[0]
    assert prediction.confidence == 0.91
    assert prediction.confidence_level is PredictionConfidenceLevel.VERY_HIGH


def test_v93_builds_prediction_from_rule() -> None:
    result = execute({
        "theory": theory_context()["theory"],
        "prediction_rules": [{
            "id": "rule-1",
            "if": "la reconnaissance est répétée",
            "then": "la stabilité augmente",
            "source_claim_ids": ["c1"],
        }],
    })
    assert result.scientific_predictions[0].text == (
        "Si la reconnaissance est répétée, alors la stabilité augmente."
    )
    assert "la reconnaissance est répétée" in result.scientific_predictions[0].assumptions


def test_v93_simulates_scenarios_deterministically() -> None:
    context = theory_context()
    context["scenarios"] = [
        {
            "id": "s-supported",
            "name": "Répétition maintenue",
            "assumptions": ["la répétition est maintenue"],
            "variables": {"confidence_modifier": 0.03},
        },
        {
            "id": "s-conditional",
            "name": "Répétition interrompue",
            "assumptions": [],
        },
    ]
    result = execute(context)
    simulations = {item.scenario_id: item for item in result.scenario_simulations}
    assert simulations["s-supported"].outcome == "supported_by_scenario"
    assert simulations["s-conditional"].outcome == "conditional"
    assert simulations["s-supported"].adjusted_confidence > simulations["s-conditional"].adjusted_confidence


def test_v93_serialization_and_operator_trace() -> None:
    context = theory_context()
    context["scenarios"] = [{"id": "s1", "name": "Scénario", "assumptions": []}]
    result = execute(context)
    payload = result.to_dict()
    assert payload["scientific_predictions"][0]["confidence_level"]
    assert payload["scientific_scenarios"][0]["scenario_id"] == "s1"
    assert payload["scenario_simulations"][0]["prediction_id"] == "p1"
    trace = next(item for item in result.operator_trace if item.stage.value == "prediction")
    assert trace.operator == "PredictionOperator"
    assert "scenario_simulations" in trace.outputs
