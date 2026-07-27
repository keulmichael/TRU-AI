from __future__ import annotations

import json

from tru_ai.cognitive.reasoning.models import (
    ReflexiveGraph,
    ReflexiveLoop,
    ReflexiveRelation,
    ReasoningPlan,
    ReasoningResult,
    ReasoningStage,
)


def test_reflexive_relation_to_dict() -> None:
    relation = ReflexiveRelation(
        observer="sujet",
        observed="objet",
        relation="observe",
        recognition_level=1,
        confidence=0.9,
    )

    assert relation.to_dict() == {
        "observer": "sujet",
        "observed": "objet",
        "relation": "observe",
        "recognition_level": 1,
        "confidence": 0.9,
    }


def test_reflexive_loop_to_dict() -> None:
    relation = ReflexiveRelation(
        observer="sujet",
        observed="objet",
        relation="observe",
        recognition_level=1,
    )
    loop = ReflexiveLoop(
        relations=(relation,),
        closed=False,
    )

    assert loop.to_dict() == {
        "relations": [
            {
                "observer": "sujet",
                "observed": "objet",
                "relation": "observe",
                "recognition_level": 1,
                "confidence": None,
            }
        ],
        "closed": False,
    }


def test_reflexive_graph_to_dict() -> None:
    relation = ReflexiveRelation(
        observer="sujet",
        observed="objet",
        relation="observe",
        recognition_level=2,
        confidence=1.0,
    )
    loop = ReflexiveLoop(
        relations=(relation,),
        closed=True,
    )
    graph = ReflexiveGraph(
        relations=(relation,),
        loops=(loop,),
    )

    assert graph.to_dict() == {
        "relations": [
            {
                "observer": "sujet",
                "observed": "objet",
                "relation": "observe",
                "recognition_level": 2,
                "confidence": 1.0,
            }
        ],
        "loops": [
            {
                "relations": [
                    {
                        "observer": "sujet",
                        "observed": "objet",
                        "relation": "observe",
                        "recognition_level": 2,
                        "confidence": 1.0,
                    }
                ],
                "closed": True,
            }
        ],
    }


def test_reasoning_stage_contains_reflexivity() -> None:
    assert ReasoningStage.REFLEXIVITY.value == "reflexivity"


def test_reasoning_result_contains_reflexive_defaults() -> None:
    plan = ReasoningPlan(
        question="Question",
        intent="test",
        steps=(),
    )

    result = ReasoningResult(plan=plan)

    assert result.reflexive_graph == ReflexiveGraph()
    assert result.reflexive_relations == ()
    assert result.reflexive_loops == ()


def test_reasoning_result_serializes_reflexive_data() -> None:
    relation = ReflexiveRelation(
        observer="sujet",
        observed="sujet",
        relation="se_reconnait",
        recognition_level=3,
        confidence=0.8,
    )
    loop = ReflexiveLoop(
        relations=(relation,),
        closed=True,
    )
    graph = ReflexiveGraph(
        relations=(relation,),
        loops=(loop,),
    )
    plan = ReasoningPlan(
        question="Comment le sujet se reconnaît-il ?",
        intent="concept_explanation",
        steps=(),
    )
    result = ReasoningResult(
        plan=plan,
        reflexive_graph=graph,
        reflexive_relations=(relation,),
        reflexive_loops=(loop,),
    )

    payload = result.to_dict()

    assert payload["reflexive_graph"] == graph.to_dict()
    assert payload["reflexive_relations"] == [relation.to_dict()]
    assert payload["reflexive_loops"] == [loop.to_dict()]
    assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload