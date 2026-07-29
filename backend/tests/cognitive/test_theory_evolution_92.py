from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
)


def execute(context: dict):
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Fais évoluer la théorie.", intent="theory_evolution")
    )
    return ReasoningExecutor().execute(plan, conversation_context=context)


def test_v92_creates_versioned_snapshot_and_history() -> None:
    result = execute({
        "theory_version": "0.9.2",
        "theory": {
            "id": "tru",
            "name": "TRU",
            "claims": [{"id": "c1", "text": "La reconnaissance transforme la relation.", "status": "supported", "evidence": ["A"]}],
        },
        "baseline_theory": {"claims": []},
    })
    assert result.theory_history.current_snapshot_id == "tru@0.9.2"
    assert result.theory_history.snapshots[-1].version == "0.9.2"
    assert result.theory_history.snapshots[-1].propositions == result.theory.propositions


def test_v92_preserves_and_extends_explicit_history() -> None:
    result = execute({
        "theory": {"id": "tru", "claims": [{"text": "Proposition actuelle."}]},
        "theory_history": {
            "snapshots": [{
                "snapshot_id": "tru@1.0", "theory_id": "tru", "version": "1.0",
                "claims": [{"id": "old", "text": "Proposition ancienne.", "status": "partial"}],
            }]
        },
    })
    assert [s.version for s in result.theory_history.snapshots] == ["1.0", "1.1"]
    assert result.theory_history.snapshots[-1].parent_snapshot_id == "tru@1.0"


def test_v92_exposes_tru_operator_trace() -> None:
    result = execute({"theory": {"claims": [{"text": "Une proposition."}]}})
    operators = {trace.operator for trace in result.operator_trace}
    assert "ObservationOperator" in operators
    assert "TheoryEvolutionOperator" in operators
    assert "ManifestationOperator" in operators
    assert all(trace.status.value == "success" for trace in result.operator_trace)


def test_v92_serialization_exposes_history_and_trace() -> None:
    payload = execute({"theory": {"id": "tru", "claims": [{"text": "Une proposition."}]}}).to_dict()
    assert payload["theory_history"]["theory_id"] == "tru"
    assert payload["operator_trace"]
    assert payload["operator_trace"][0]["operator"].endswith("Operator")
