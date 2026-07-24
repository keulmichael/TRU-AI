from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

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
