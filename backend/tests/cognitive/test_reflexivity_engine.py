from __future__ import annotations

import json

from tru_ai.cognitive.reasoning import (
    ReasoningExecutor,
    ReasoningPlanner,
    ReasoningRequest,
    ReasoningStage,
)


def _execute_reflexivity(recognition_graph: dict[str, object]):
    plan = ReasoningPlanner().plan(
        ReasoningRequest(
            question="Analyse les relations réflexives.",
            intent="reflexivity_review",
        )
    )
    return ReasoningExecutor().execute(
        plan,
        conversation_context={"recognition_graph": recognition_graph},
    )


def test_reflexivity_review_contains_reflexivity_stage() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(
            question="Analyse la réflexivité.",
            intent="reflexivity_review",
        )
    )
    stages = tuple(step.stage for step in plan.steps)
    assert ReasoningStage.RECOGNITION in stages
    assert ReasoningStage.DELTA in stages
    assert ReasoningStage.REFLEXIVITY in stages
    assert stages.index(ReasoningStage.REFLEXIVITY) > stages.index(
        ReasoningStage.DELTA
    )


def test_reflexivity_engine_preserves_explicit_relation() -> None:
    result = _execute_reflexivity({
        "nodes": [
            {"id": "sujet", "label": "Sujet"},
            {"id": "objet", "label": "Objet"},
        ],
        "relations": [{
            "id": "r1",
            "source": "sujet",
            "target": "objet",
            "type": "observe",
            "attributes": {"confidence": 0.9},
        }],
    })
    relation = result.reflexive_relations[0]
    assert relation.observer == "sujet"
    assert relation.observed == "objet"
    assert relation.relation == "observe"
    assert relation.recognition_level == 1
    assert relation.confidence == 0.9
    assert result.reflexive_loops == ()


def test_reflexivity_engine_detects_self_relation() -> None:
    result = _execute_reflexivity({
        "nodes": [{"id": "sujet", "label": "Sujet"}],
        "relations": [{
            "id": "r1",
            "source": "sujet",
            "target": "sujet",
            "type": "se_reconnait",
        }],
    })
    assert result.reflexive_relations[0].recognition_level == 3
    assert len(result.reflexive_loops) == 1
    assert result.reflexive_loops[0].closed is True


def test_reflexivity_engine_detects_reciprocal_loop_once() -> None:
    result = _execute_reflexivity({
        "nodes": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"},
        ],
        "relations": [
            {"id": "r1", "source": "a", "target": "b", "type": "reconnait"},
            {"id": "r2", "source": "b", "target": "a", "type": "reconnait"},
        ],
    })
    assert len(result.reflexive_relations) == 2
    assert {r.recognition_level for r in result.reflexive_relations} == {2}
    assert len(result.reflexive_loops) == 1
    assert tuple(r.observer for r in result.reflexive_loops[0].relations) == (
        "a", "b"
    )


def test_reflexivity_engine_detects_three_node_cycle_once() -> None:
    result = _execute_reflexivity({
        "nodes": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"},
            {"id": "c", "label": "C"},
        ],
        "relations": [
            {"id": "r1", "source": "a", "target": "b", "type": "agit"},
            {"id": "r2", "source": "b", "target": "c", "type": "agit"},
            {"id": "r3", "source": "c", "target": "a", "type": "agit"},
        ],
    })
    assert len(result.reflexive_loops) == 1
    assert tuple(r.observer for r in result.reflexive_loops[0].relations) == (
        "a", "b", "c"
    )
    assert all(r.recognition_level == 2 for r in result.reflexive_relations)


def test_reflexivity_engine_does_not_invent_relations() -> None:
    result = _execute_reflexivity({
        "nodes": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"},
        ],
        "relations": [],
    })
    assert result.reflexive_relations == ()
    assert result.reflexive_loops == ()


def test_invalid_confidence_is_not_preserved() -> None:
    result = _execute_reflexivity({
        "nodes": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"},
        ],
        "relations": [{
            "id": "r1",
            "source": "a",
            "target": "b",
            "type": "observe",
            "attributes": {"confidence": 4},
        }],
    })
    assert result.reflexive_relations[0].confidence is None


def test_reflexivity_result_is_json_serializable() -> None:
    result = _execute_reflexivity({
        "nodes": [{"id": "a", "label": "A"}],
        "relations": [{
            "id": "r1",
            "source": "a",
            "target": "a",
            "type": "se_reconnait",
        }],
    })
    payload = result.to_dict()
    assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload
    assert payload["reflexive_graph"]["loops"]
