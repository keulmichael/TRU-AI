from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from tru_ai import __version__
from tru_ai.cognitive.reasoning import ReasoningExecutor, ReasoningPlanner
from tru_ai.scientific.models import (
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
)
from tru_ai.scientific.service import ScientificService


router = APIRouter(
    prefix="/scientific",
    tags=["Scientific analysis"],
)


@lru_cache(maxsize=1)
def get_scientific_service() -> ScientificService:
    """Return the application facade for scientific analysis."""

    return ScientificService()


@router.get("/health")
def scientific_health() -> dict[str, bool | str]:
    """Report availability of the generic scientific API dependencies."""

    service_available = _can_create(ScientificService)
    planner_available = _can_create(ReasoningPlanner)
    executor_available = _can_create(ReasoningExecutor)
    available = service_available and planner_available and executor_available
    return {
        "status": "ok" if available else "degraded",
        "version": __version__,
        "scientific_service_available": service_available,
        "planner_available": planner_available,
        "executor_available": executor_available,
    }


@router.post("/analyze", response_model=ScientificAnalysisResult)
def scientific_analyze(
    payload: ScientificAnalysisRequest,
) -> ScientificAnalysisResult:
    """Expose ScientificService without adding scientific logic."""

    try:
        return get_scientific_service().analyze(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Scientific analysis failed.",
        ) from error


def _can_create(factory: type[object]) -> bool:
    try:
        factory()
    except Exception:
        return False
    return True
