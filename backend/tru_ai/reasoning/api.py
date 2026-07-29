from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tru_ai.cognitive.reasoning import (
    ReasoningExecutor as CognitiveReasoningExecutor,
    ReasoningPlanner as CognitiveReasoningPlanner,
    ReasoningRequest as CognitiveReasoningRequest,
)
from tru_ai.reasoning.models import (
    ProofTreeNode,
    ReasoningExplanation,
)
from tru_ai.reasoning.repository import (
    ReasoningRepository,
)


router = APIRouter(
    prefix="/reasoning",
    tags=["Reasoning explanations"],
)


class ScientificDemoPredictionRule(BaseModel):
    id: str = Field(default="rule-stability", min_length=1)
    statement: str = Field(
        default="La répétition de la reconnaissance augmente la stabilité.",
        min_length=1,
    )
    condition: str = Field(
        default="la reconnaissance est répétée",
        min_length=1,
    )
    consequence: str | None = None
    confidence: float | None = Field(default=0.85, ge=0.0, le=1.0)
    expected_observation: str = Field(
        default="Hausse mesurable de la stabilité.",
        min_length=1,
    )
    falsification_condition: str = Field(
        default="La stabilité diminue malgré la répétition.",
        min_length=1,
    )
    horizon: str | None = "trois cycles"


class ScientificDemoRequest(BaseModel):
    observation: str = Field(
        default="La reconnaissance répétée ne stabilise pas cette relation.",
        min_length=1,
    )
    claims: list[str] = Field(
        default_factory=lambda: [
            "La reconnaissance répétée stabilise une relation.",
            "Une relation stabilisée rend les prédictions plus robustes.",
        ],
        min_length=1,
    )
    prediction_rule: ScientificDemoPredictionRule = Field(
        default_factory=ScientificDemoPredictionRule
    )
    compatibility_score: float = Field(default=0.12, ge=0.0, le=1.0)
    matches_falsification_condition: bool = True


PROJECT_ROOT = Path(__file__).resolve().parents[3]

GRAPH_INFERRED_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph_inferred"
)

INFERENCE_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "inference"
)

REASONING_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "reasoning"
)

SCIENTIFIC_DEMO_STAGES = (
    "observation",
    "theory_evolution",
    "prediction",
    "verification",
    "falsification",
    "scientific_gaps",
)


def _claim_payloads(claims: list[str]) -> list[dict]:
    return [
        {
            "id": f"c{index}",
            "text": claim,
            "status": "supported" if index == 1 else "partial",
            "evidence": [f"evidence-{index}"],
            "confidence": 0.86 if index == 1 else 0.62,
        }
        for index, claim in enumerate(claims, start=1)
        if claim.strip()
    ]


def _build_scientific_demo_context(payload: ScientificDemoRequest) -> dict:
    claims = _claim_payloads(payload.claims)
    first_claim_id = claims[0]["id"] if claims else "c1"
    rule = payload.prediction_rule
    return {
        "theory_version": "0.9.5-dev-demo",
        "theory": {
            "id": "tru-scientific-demo",
            "name": "TRU-AI scientific demo",
            "claims": claims,
        },
        "baseline_theory": {
            "claims": [
                {
                    "id": "baseline-c1",
                    "text": "La reconnaissance peut transformer une relation.",
                    "status": "partial",
                }
            ]
        },
        "theory_history": {
            "snapshots": [
                {
                    "snapshot_id": "tru-scientific-demo@0.9.4",
                    "theory_id": "tru-scientific-demo",
                    "version": "0.9.4",
                    "claims": [
                        {
                            "id": "old-c1",
                            "text": "La reconnaissance peut transformer une relation.",
                            "status": "partial",
                        }
                    ],
                }
            ]
        },
        "predictions": [] if rule.consequence else [
            {
                "id": rule.id,
                "text": rule.statement,
                "source_claim_ids": [first_claim_id],
                "confidence": rule.confidence,
                "assumptions": [rule.condition],
                "expected_observation": rule.expected_observation,
                "falsification_condition": rule.falsification_condition,
                "horizon": rule.horizon,
            }
        ],
        "prediction_rules": [
            {
                "id": rule.id,
                "if": rule.condition,
                "then": rule.consequence,
                "source_claim_ids": [first_claim_id],
                "confidence": rule.confidence,
                "expected_observation": rule.expected_observation,
                "falsification_condition": rule.falsification_condition,
                "horizon": rule.horizon,
            }
        ] if rule.consequence else [],
        "scenarios": [
            {
                "id": "scenario-demo",
                "name": "Reconnaissance répétée",
                "assumptions": [rule.condition],
                "variables": {"confidence_modifier": 0.02},
            }
        ],
        "scientific_observations": [
            {
                "id": "observation-demo",
                "prediction_id": rule.id,
                "text": payload.observation,
                "compatibility_score": payload.compatibility_score,
                "matches_falsification_condition": (
                    payload.matches_falsification_condition
                ),
                "evidence_ids": ["demo-measure"],
            }
        ],
    }


def _summary(raw_result: dict) -> dict:
    theory_maturity = raw_result.get("theory", {}).get("maturity", {})
    predictions = raw_result.get("scientific_predictions", [])
    simulations = raw_result.get("scenario_simulations", [])
    verifications = raw_result.get("verification_reports", [])
    falsifications = raw_result.get("falsification_reports", [])
    revisions = raw_result.get("scientific_theory_revisions", [])
    prediction = predictions[0] if predictions else {}
    simulation = simulations[0] if simulations else {}
    verification = verifications[0] if verifications else {}
    falsification = falsifications[0] if falsifications else {}
    revision = revisions[0] if revisions else {}
    return {
        "theory_maturity": theory_maturity,
        "prediction_confidence": prediction.get("confidence"),
        "prediction_confidence_level": prediction.get("confidence_level"),
        "scenario_adjusted_confidence": simulation.get("adjusted_confidence"),
        "verification_status": verification.get("status"),
        "verification_consistency_score": verification.get(
            "consistency_score"
        ),
        "verification_evidence_score": verification.get("evidence_score"),
        "falsified": falsification.get("falsified"),
        "revision_required": falsification.get("revision_required"),
        "final_action": revision.get("action"),
    }


def _first_item(raw_result: dict, key: str) -> dict:
    values = raw_result.get(key, [])
    return values[0] if values else {}


def _unknown() -> str:
    return "Non déterminé par cette exécution."


def _build_human_readable(raw_result: dict) -> dict:
    theory = raw_result.get("theory", {})
    theory_graph = raw_result.get("theory_graph", {})
    prediction = _first_item(raw_result, "scientific_predictions")
    scenario = _first_item(raw_result, "scientific_scenarios")
    simulation = _first_item(raw_result, "scenario_simulations")
    observation = _first_item(raw_result, "scientific_observations")
    verification = _first_item(raw_result, "verification_reports")
    falsification = _first_item(raw_result, "falsification_reports")
    revision = _first_item(raw_result, "scientific_theory_revisions")
    gaps = raw_result.get("scientific_gaps", [])
    evolution = raw_result.get("theory_evolution", {})
    maturity = theory.get("maturity", {})

    predicted = prediction.get("text") or _unknown()
    observed = observation.get("text") or _unknown()
    expected = prediction.get("expected_observation") or _unknown()
    verification_status = verification.get("status") or _unknown()
    falsified = falsification.get("falsified")
    revision_required = falsification.get("revision_required")
    action = revision.get("action") or _unknown()

    conclusion_parts = [
        f"La théorie prédit : {predicted}",
        f"L'observation reçue indique : {observed}",
    ]
    if verification_status != _unknown():
        conclusion_parts.append(
            f"Le résultat de vérification est : {verification_status}."
        )
    if verification_status == "contradicted":
        conclusion_parts.append("La prédiction est donc contredite.")
    elif verification_status == "confirmed":
        conclusion_parts.append("La prédiction est confirmée par l'observation.")
    elif verification_status != _unknown():
        conclusion_parts.append(
            "La comparaison ne suffit pas à confirmer ou contredire fortement la prédiction."
        )
    if falsified is True:
        conclusion_parts.append("La formulation actuelle de la théorie est falsifiée.")
    elif falsified is False:
        conclusion_parts.append("Aucune falsification formelle n'est établie.")
    if revision_required is True:
        conclusion_parts.append("Une révision est nécessaire.")
    elif revision_required is False:
        conclusion_parts.append("Aucune révision obligatoire n'est produite.")
    conclusion_parts.append(f"Action proposée : {action}.")
    if gaps:
        descriptions = [
            gap.get("description", "")
            for gap in gaps
            if gap.get("description")
        ]
        if descriptions:
            conclusion_parts.append(
                "Variable ou limite identifiée : " + "; ".join(descriptions)
            )
    elif verification.get("limitations"):
        conclusion_parts.append(
            "Variable ou limite identifiée : "
            + "; ".join(verification["limitations"])
        )

    observation_explanation = (
        f"Le moteur reçoit l'observation « {observed} ». "
        "Aucun concept de reconnaissance supplémentaire n'est produit par ce cas."
    )
    if observation.get("matches_falsification_condition") is True:
        observation_explanation += (
            " L'observation signale une condition de falsification potentiellement atteinte."
        )

    added = evolution.get("added_claims", [])
    removed = evolution.get("removed_claims", [])
    strengthened = evolution.get("strengthened_claims", [])
    weakened = evolution.get("weakened_claims", [])
    theory_evolution_explanation = (
        "Le moteur compare la théorie courante à l'état de référence. "
        f"Claims ajoutés : {len(added)} ; supprimés : {len(removed)} ; "
        f"renforcés : {len(strengthened)} ; affaiblis : {len(weakened)}. "
        f"La maturité calculée est {maturity.get('score', _unknown())}."
    )

    prediction_explanation = (
        f"La règle produit la prédiction « {predicted} ». "
        f"La confiance est {prediction.get('confidence', _unknown())} "
        f"avec le niveau {prediction.get('confidence_level', _unknown())}."
    )
    if scenario:
        prediction_explanation += (
            f" Le scénario « {scenario.get('name', _unknown())} » aboutit à "
            f"{simulation.get('outcome', _unknown())}."
        )

    verification_explanation = (
        f"Le moteur attendait « {expected} », mais l'observation indique « {observed} ». "
        f"Le statut retourné est {verification_status}, avec un score de cohérence "
        f"de {verification.get('consistency_score', _unknown())} et un score de preuve "
        f"de {verification.get('evidence_score', _unknown())}."
    )

    falsification_explanation = (
        f"Condition de falsification : {prediction.get('falsification_condition') or _unknown()} "
        f"Condition atteinte : {falsification.get('falsification_condition_met', _unknown())}. "
        f"Test formel possible : {falsification.get('formal_test_possible', _unknown())}. "
        f"Falsifié : {falsified if falsified is not None else _unknown()}. "
        f"Révision nécessaire : {revision_required if revision_required is not None else _unknown()}. "
        f"Action recommandée : {action}."
    )

    if gaps:
        descriptions = [
            gap.get("description", "")
            for gap in gaps
            if gap.get("description")
        ]
        scientific_gaps_explanation = (
            "Lacunes détectées : " + "; ".join(descriptions)
            if descriptions
            else _unknown()
        )
    else:
        scientific_gaps_explanation = (
            "Aucune lacune scientifique supplémentaire n'a été détectée par ce cas."
        )

    claims = theory_graph.get("claims", [])
    recognized = "; ".join(
        claim.get("text", "")
        for claim in claims
        if claim.get("text")
    ) or _unknown()
    learning = (
        f"Le système doit appliquer l'action « {action} »."
        if action != _unknown()
        else _unknown()
    )
    return {
        "conclusion": "\n\n".join(conclusion_parts),
        "observation_explanation": observation_explanation,
        "theory_evolution_explanation": theory_evolution_explanation,
        "prediction_explanation": prediction_explanation,
        "verification_explanation": verification_explanation,
        "falsification_explanation": falsification_explanation,
        "scientific_gaps_explanation": scientific_gaps_explanation,
        "reflexive_view": {
            "observed": observed,
            "recognized": recognized,
            "predicted": predicted,
            "confirmed_or_refuted_by": (
                verification.get("rationale") or _unknown()
            ),
            "learning": learning,
        },
    }


def _stage_cards(raw_result: dict) -> list[dict]:
    trace_by_stage = {
        item["stage"]: item
        for item in raw_result.get("operator_trace", [])
    }
    summary = _summary(raw_result)
    human_readable = _build_human_readable(raw_result)
    data_by_stage = {
        "observation": {
            "input": _first_item(raw_result, "scientific_observations"),
            "output": raw_result.get("plan", {}).get("steps", [])[0],
            "score": None,
            "decision": "Observation reçue",
        },
        "theory_evolution": {
            "input": raw_result.get("theory_graph"),
            "output": raw_result.get("theory_evolution"),
            "score": summary["theory_maturity"].get("score"),
            "decision": raw_result.get("theory_history", {}).get(
                "current_snapshot_id"
            ),
        },
        "prediction": {
            "input": raw_result.get("theory_graph"),
            "output": raw_result.get("scientific_predictions"),
            "score": summary["prediction_confidence"],
            "decision": summary["prediction_confidence_level"],
        },
        "verification": {
            "input": raw_result.get("scientific_observations"),
            "output": raw_result.get("verification_reports"),
            "score": summary["verification_consistency_score"],
            "decision": summary["verification_status"],
        },
        "falsification": {
            "input": raw_result.get("verification_reports"),
            "output": raw_result.get("falsification_reports"),
            "score": summary["verification_evidence_score"],
            "decision": (
                "falsified"
                if summary["falsified"]
                else "not_falsified"
            ),
        },
        "scientific_gaps": {
            "input": raw_result.get("theory_graph"),
            "output": raw_result.get("scientific_gaps"),
            "score": len(raw_result.get("scientific_gaps", [])),
            "decision": "complete" if not raw_result.get("scientific_gaps") else "gaps",
        },
    }
    explanation_by_stage = {
        "observation": human_readable["observation_explanation"],
        "theory_evolution": human_readable["theory_evolution_explanation"],
        "prediction": human_readable["prediction_explanation"],
        "verification": human_readable["verification_explanation"],
        "falsification": human_readable["falsification_explanation"],
        "scientific_gaps": human_readable["scientific_gaps_explanation"],
    }
    return [
        {
            "stage": stage,
            "operator": trace_by_stage.get(stage, {}).get("operator"),
            "status": trace_by_stage.get(stage, {}).get("status"),
            "inputs": trace_by_stage.get(stage, {}).get("inputs", []),
            "outputs": trace_by_stage.get(stage, {}).get("outputs", []),
            "score": data_by_stage[stage]["score"],
            "decision": data_by_stage[stage]["decision"],
            "explanation": explanation_by_stage[stage],
            "data": data_by_stage[stage],
        }
        for stage in SCIENTIFIC_DEMO_STAGES
    ]


def _scientific_demo_response(payload: ScientificDemoRequest) -> dict:
    request = CognitiveReasoningRequest(
        question="Démonstration du pipeline scientifique TRU-AI",
        intent="scientific_research",
    )
    plan = CognitiveReasoningPlanner().plan(request)
    result = CognitiveReasoningExecutor().execute(
        plan,
        conversation_context=_build_scientific_demo_context(payload),
    )
    raw_result = result.to_dict()
    return {
        "execution_plan": raw_result["plan"],
        "theory_evolution": raw_result["theory_evolution"],
        "theory_history": raw_result["theory_history"],
        "scientific_predictions": raw_result["scientific_predictions"],
        "scientific_scenarios": raw_result["scientific_scenarios"],
        "scenario_simulations": raw_result["scenario_simulations"],
        "verification_reports": raw_result["verification_reports"],
        "falsification_reports": raw_result["falsification_reports"],
        "scientific_theory_revisions": (
            raw_result["scientific_theory_revisions"]
        ),
        "scientific_gaps": raw_result["scientific_gaps"],
        "operator_trace": raw_result["operator_trace"],
        "summary": _summary(raw_result),
        "human_readable": _build_human_readable(raw_result),
        "stage_cards": _stage_cards(raw_result),
        "raw_result": raw_result,
    }


@dataclass(frozen=True)
class ReasoningStore:
    explanations_by_edge_id: dict[
        str,
        ReasoningExplanation,
    ]
    proof_trees_by_edge_id: dict[
        str,
        ProofTreeNode,
    ]

    @property
    def explanation_count(self) -> int:
        return len(
            self.explanations_by_edge_id
        )

    @property
    def proof_tree_count(self) -> int:
        return len(
            self.proof_trees_by_edge_id
        )


@lru_cache(maxsize=1)
def get_store() -> ReasoningStore:
    repository = ReasoningRepository(
        graph_inferred_directory=(
            GRAPH_INFERRED_DIRECTORY
        ),
        inference_directory=(
            INFERENCE_DIRECTORY
        ),
        reasoning_directory=(
            REASONING_DIRECTORY
        ),
    )
    result = repository.load_reasoning_result()

    return ReasoningStore(
        explanations_by_edge_id={
            explanation.inferred_edge_id: (
                explanation
            )
            for explanation
            in result.explanations
        },
        proof_trees_by_edge_id={
            proof_tree.edge_id: proof_tree
            for proof_tree in result.proof_trees
        },
    )


@router.get("/health")
def reasoning_health() -> dict:
    try:
        store = get_store()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "status": "ok",
        "loaded": True,
        "explanation_count": (
            store.explanation_count
        ),
        "proof_tree_count": (
            store.proof_tree_count
        ),
    }


@router.post("/reload")
def reload_reasoning() -> dict:
    get_store.cache_clear()

    try:
        store = get_store()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "status": "reloaded",
        "loaded": True,
        "explanation_count": (
            store.explanation_count
        ),
        "proof_tree_count": (
            store.proof_tree_count
        ),
    }


@router.post("/scientific-demo")
def scientific_demo(payload: ScientificDemoRequest) -> dict:
    try:
        return _scientific_demo_response(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/explain/{edge_id}")
def explain_edge(
    edge_id: str,
) -> dict:
    try:
        store = get_store()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    explanation = (
        store.explanations_by_edge_id.get(
            edge_id
        )
    )

    if explanation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Explication introuvable : "
                f"{edge_id}"
            ),
        )

    return explanation.to_dict()


@router.get("/proof/{edge_id}")
def proof_tree(
    edge_id: str,
) -> dict:
    try:
        store = get_store()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    proof = store.proof_trees_by_edge_id.get(
        edge_id
    )

    if proof is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Arbre de preuve introuvable : "
                f"{edge_id}"
            ),
        )

    return proof.to_dict()
