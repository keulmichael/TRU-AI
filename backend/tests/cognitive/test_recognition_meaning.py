import pytest
from tru_ai.cognitive.reasoning import (
    RecognitionGapType,
    RecognitionMeaningEngine,
    ReasoningExecutor,
    ReasoningRequest,
    ReasoningStage,
)
from tru_ai.cognitive.reasoning.engines.base import ReasoningExecutionState
from tru_ai.cognitive.reasoning.models import ReasoningStep
from tru_ai.cognitive.reasoning.planner import ReasoningPlanner
from tru_ai.cognitive.reasoning.engines.recognition import RecognitionEngine
from tru_ai.cognitive.reasoning.engines.reflexivity import ReflexivityEngine


def step(stage: ReasoningStage) -> ReasoningStep:
    return ReasoningStep(position=1, stage=stage, objective="Test")


def build_state() -> ReasoningExecutionState:
    state = ReasoningExecutionState(
        question="Que reconnaît A ?",
        intent="recognition_meaning_review",
        conversation_context={
            "recognition_graph": {
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                    {
                        "id": "c",
                        "label": "C",
                        "attributes": {"recognition_status": "searched"},
                    },
                ],
                "relations": [
                    {"id": "r1", "source": "a", "target": "b", "type": "recognizes"},
                    {"id": "r2", "source": "b", "target": "a", "type": "recognizes"},
                ],
            }
        },
    )
    RecognitionEngine().execute(step=step(ReasoningStage.RECOGNITION), state=state)
    ReflexivityEngine().execute(step=step(ReasoningStage.REFLEXIVITY), state=state)
    return state


def test_engine_describes_recognized_objects_deterministically() -> None:
    state = build_state()
    output = RecognitionMeaningEngine().execute(
        step=step(ReasoningStage.RECOGNITION_MEANING), state=state
    )
    assert len(state.recognition_meanings) == 2
    assert all(item.reciprocal for item in state.recognition_meanings)
    assert all(item.stable for item in state.recognition_meanings)
    assert output["recognition_completeness"]["score"] == pytest.approx(2 / 3)


def test_engine_keeps_structural_and_explicit_gaps_distinct() -> None:
    state = build_state()
    RecognitionMeaningEngine().execute(
        step=step(ReasoningStage.RECOGNITION_MEANING), state=state
    )
    c_gaps = [gap for gap in state.recognition_gaps if gap.object_id == "c"]
    assert {gap.gap_type for gap in c_gaps} == {
        RecognitionGapType.STRUCTURAL,
        RecognitionGapType.SEARCHED,
    }


def test_full_executor_exposes_recognition_meaning_graph() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(
            question="Que reconnaît A ?",
            intent="recognition_meaning_review",
        )
    )
    result = ReasoningExecutor().execute(
        plan,
        conversation_context=build_state().conversation_context,
    )
    assert ReasoningStage.RECOGNITION_MEANING in {
        item.stage for item in result.plan.steps
    }
    assert len(result.recognition_meanings) == 2
    assert result.recognition_meaning_graph.completeness.total_objects == 3
    assert "signification de la reconnaissance" in (result.synthesis or "")


def test_result_serialization_contains_new_fields() -> None:
    plan = ReasoningPlanner().plan(
        ReasoningRequest(question="Analyse.", intent="recognition_meaning_review")
    )
    payload = ReasoningExecutor().execute(plan, conversation_context={}).to_dict()
    assert "recognition_meaning_graph" in payload
    assert isinstance(payload["recognition_meanings"], list)
    assert isinstance(payload["recognition_gaps"], list)
