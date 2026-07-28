from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
    TheoryClaimStatus,
    TheoryPropositionRole,
)


def _execute(context: dict):
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Construis la théorie.", intent="scientific_research")
    )
    return ReasoningExecutor().execute(plan, conversation_context=context)


def test_builder_deduplicates_equivalent_propositions() -> None:
    result = _execute({
        "theory": {
            "id": "tru",
            "claims": [
                {"id": "c1", "text": "La reconnaissance transforme la relation.", "evidence": ["A"]},
                {"id": "c2", "text": "  La reconnaissance transforme la relation  ", "evidence": ["B"]},
            ],
        }
    })
    assert len(result.theory.propositions) == 1
    assert len(result.theory.evidence) == 2
    assert result.theory.revisions[0].action == "merged"


def test_builder_promotes_strongly_corroborated_proposition_to_axiom() -> None:
    result = _execute({
        "theory": {
            "claims": [{
                "id": "c1",
                "text": "La reconnaissance transforme la relation.",
                "status": "supported",
                "evidence": ["Observation A", "Observation B"],
                "confidence": 0.9,
            }]
        }
    })
    proposition = result.theory.propositions[0]
    assert proposition.role is TheoryPropositionRole.AXIOM
    assert result.theory.axioms == (proposition,)


def test_builder_keeps_unsupported_claim_as_hypothesis() -> None:
    result = _execute({"theory": {"claims": [{"id": "h1", "text": "Une hypothèse."}]}})
    proposition = result.theory.propositions[0]
    assert proposition.role is TheoryPropositionRole.HYPOTHESIS
    assert proposition.status is TheoryClaimStatus.UNSUPPORTED


def test_builder_computes_bounded_maturity() -> None:
    result = _execute({
        "theory": {
            "claims": [
                {"text": "Proposition soutenue.", "status": "supported", "evidence": ["A"]},
                {"text": "Proposition ouverte."},
            ]
        }
    })
    assert 0.0 <= result.theory.maturity.score <= 1.0
    assert result.theory.maturity.level in {"embryonic", "developing", "mature"}


def test_result_serialization_exposes_complete_theory() -> None:
    payload = _execute({"theory": {"id": "tru", "name": "TRU", "claims": [{"text": "Proposition."}]}}).to_dict()
    assert payload["theory"]["theory_id"] == "tru"
    assert payload["theory"]["title"] == "TRU"
    assert isinstance(payload["theory"]["propositions"], list)
    assert "maturity" in payload["theory"]
