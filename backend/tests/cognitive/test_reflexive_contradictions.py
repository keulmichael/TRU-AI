from __future__ import annotations

from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
)


def _execute(context: dict[str, object]):
    plan = ReasoningPlanner().plan(
        ReasoningRequest(
            question="Analyse la cohérence réflexive.",
            intent="concept_explanation",
        )
    )
    return ReasoningExecutor().execute(
        plan,
        conversation_context=context,
    )


def test_synthesis_reports_explicit_reflexive_contradictions_separately() -> None:
    result = _execute(
        {
            "recognition_graph": {
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                ],
                "relations": [
                    {
                        "id": "r1",
                        "source": "a",
                        "target": "b",
                        "type": "relation",
                        "attributes": {"polarity": "positive"},
                    },
                    {
                        "id": "r2",
                        "source": "a",
                        "target": "b",
                        "type": "relation",
                        "attributes": {"polarity": "negative"},
                    },
                ],
            }
        }
    )

    assert "1 contradiction(s) réflexive(s) explicite(s)" in (
        result.synthesis or ""
    )
    assert "0 tension(s) potentielle(s)" in (result.synthesis or "")


def test_synthesis_reports_potential_tensions_separately() -> None:
    result = _execute(
        {
            "recognition_graph": {
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                ],
                "relations": [
                    {
                        "id": "r1",
                        "source": "a",
                        "target": "b",
                        "type": "observe",
                        "attributes": {"tension": "potential"},
                    }
                ],
            }
        }
    )

    assert "0 contradiction(s) réflexive(s) explicite(s)" in (
        result.synthesis or ""
    )
    assert "1 tension(s) potentielle(s)" in (result.synthesis or "")


def test_no_metadata_means_no_invented_reflexive_conflict() -> None:
    result = _execute(
        {
            "recognition_graph": {
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                ],
                "relations": [
                    {
                        "id": "r1",
                        "source": "a",
                        "target": "b",
                        "type": "nie",
                    }
                ],
            }
        }
    )

    assert result.contradictions == ()
    assert "cohérence réflexive" not in (result.synthesis or "")
