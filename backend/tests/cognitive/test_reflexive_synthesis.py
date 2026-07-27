from __future__ import annotations

from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
)


def _execute_with_graph(
    recognition_graph: dict[str, object],
):
    plan = ReasoningPlanner().plan(
        ReasoningRequest(
            question="Produis une synthèse réflexive.",
            intent="reflexivity_review",
        )
    )

    return ReasoningExecutor().execute(
        plan,
        conversation_context={
            "recognition_graph": recognition_graph,
        },
    )


def test_synthesis_remains_unchanged_without_reflexive_data() -> None:
    result = _execute_with_graph(
        {
            "nodes": [],
            "relations": [],
        }
    )

    assert result.synthesis == (
        "Le raisonnement a identifié "
        "0 élément(s) explicite(s), "
        "0 déduction(s), "
        "0 hypothèse(s), "
        "0 contradiction(s) et "
        "0 connaissance(s) manquante(s)."
    )


def test_synthesis_reports_reflexive_relation_without_loop() -> None:
    result = _execute_with_graph(
        {
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
                }
            ],
        }
    )

    assert result.synthesis is not None
    assert (
        "L'analyse réflexive a identifié "
        "1 relation(s) réflexive(s), "
        "0 boucle(s) fermée(s), "
        "dont 0 auto-relation(s) et "
        "0 relation(s) appartenant à une boucle."
        in result.synthesis
    )


def test_synthesis_reports_self_relation() -> None:
    result = _execute_with_graph(
        {
            "nodes": [
                {"id": "a", "label": "A"},
            ],
            "relations": [
                {
                    "id": "r1",
                    "source": "a",
                    "target": "a",
                    "type": "se_reconnait",
                }
            ],
        }
    )

    assert result.synthesis is not None
    assert "1 boucle(s) fermée(s)" in result.synthesis
    assert "1 auto-relation(s)" in result.synthesis
    assert "0 relation(s) appartenant à une boucle" in result.synthesis


def test_synthesis_reports_reciprocal_loop_relations() -> None:
    result = _execute_with_graph(
        {
            "nodes": [
                {"id": "a", "label": "A"},
                {"id": "b", "label": "B"},
            ],
            "relations": [
                {
                    "id": "r1",
                    "source": "a",
                    "target": "b",
                    "type": "reconnait",
                },
                {
                    "id": "r2",
                    "source": "b",
                    "target": "a",
                    "type": "reconnait",
                },
            ],
        }
    )

    assert result.synthesis is not None
    assert "2 relation(s) réflexive(s)" in result.synthesis
    assert "1 boucle(s) fermée(s)" in result.synthesis
    assert "2 relation(s) appartenant à une boucle" in result.synthesis
