from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
    ReasoningStage,
    TheoryClaimStatus,
)


def scientific_context() -> dict:
    return {
        "theory": {
            "id": "tru",
            "name": "TRU",
            "claims": [
                {
                    "id": "c1",
                    "text": "La reconnaissance transforme la relation.",
                    "status": "supported",
                    "evidence": ["Observation A"],
                    "confidence": 0.8,
                },
                {
                    "id": "c2",
                    "text": "Toute reconnaissance est stable.",
                },
            ],
        },
        "baseline_theory": {
            "claims": [
                {"text": "La reconnaissance transforme la relation.", "status": "partial"},
                {"text": "Une ancienne proposition.", "status": "supported"},
            ]
        },
        "comparison_theories": [
            {
                "id": "other",
                "name": "Théorie B",
                "claims": [
                    {"text": "La reconnaissance transforme la relation."},
                    {"text": "La conscience ne reconnaît pas le monde."},
                ],
            }
        ],
        "predictions": [
            {
                "id": "p1",
                "text": "Une reconnaissance réciproque devrait accroître la stabilité.",
                "source_claim_ids": ["c1"],
                "falsification_condition": "Aucune différence mesurable.",
            }
        ],
    }


def test_scientific_intent_builds_complete_pipeline() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Analyse la théorie.", intent="scientific_research")
    )
    stages = tuple(step.stage for step in plan.steps)
    assert ReasoningStage.THEORY_CONSTRUCTION in stages
    assert ReasoningStage.THEORY_COMPARISON in stages
    assert ReasoningStage.THEORY_EVOLUTION in stages
    assert ReasoningStage.PREDICTION in stages
    assert ReasoningStage.SCIENTIFIC_GAPS in stages


def test_executor_constructs_and_compares_theory() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Analyse la théorie.", intent="scientific_research")
    )
    result = ReasoningExecutor().execute(plan, conversation_context=scientific_context())
    assert result.theory_graph.theory_id == "tru"
    assert len(result.theory_graph.claims) == 2
    assert result.theory_graph.claims[0].status is TheoryClaimStatus.SUPPORTED
    assert len(result.theory_comparisons) == 1
    assert result.theory_comparisons[0].shared_claims == (
        "La reconnaissance transforme la relation.",
    )


def test_executor_describes_theory_evolution() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Évolution ?", intent="theory_evolution")
    )
    result = ReasoningExecutor().execute(plan, conversation_context=scientific_context())
    assert result.theory_evolution.added_claims == ("Toute reconnaissance est stable.",)
    assert result.theory_evolution.removed_claims == ("Une ancienne proposition.",)
    assert result.theory_evolution.strengthened_claims == (
        "La reconnaissance transforme la relation.",
    )


def test_predictions_are_only_taken_from_explicit_context() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Prédictions ?", intent="scientific_research")
    )
    result = ReasoningExecutor().execute(plan, conversation_context=scientific_context())
    assert len(result.scientific_predictions) == 1
    assert result.scientific_predictions[0].source_claim_ids == ("c1",)


def test_missing_evidence_becomes_scientific_gap() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Lacunes ?", intent="scientific_research")
    )
    result = ReasoningExecutor().execute(plan, conversation_context=scientific_context())
    assert any(gap.related_claim_ids == ("c2",) for gap in result.scientific_gaps)


def test_result_serialization_exposes_scientific_fields() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Analyse.", intent="scientific_research")
    )
    payload = ReasoningExecutor().execute(
        plan, conversation_context=scientific_context()
    ).to_dict()
    assert payload["theory_graph"]["theory_id"] == "tru"
    assert isinstance(payload["theory_comparisons"], list)
    assert isinstance(payload["scientific_predictions"], list)
    assert isinstance(payload["scientific_gaps"], list)


def test_synthesis_makes_scientific_progress_visible() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Analyse.", intent="scientific_research")
    )
    result = ReasoningExecutor().execute(plan, conversation_context=scientific_context())
    assert "moteur scientifique" in (result.synthesis or "")
    assert "2 proposition(s) théorique(s)" in (result.synthesis or "")
