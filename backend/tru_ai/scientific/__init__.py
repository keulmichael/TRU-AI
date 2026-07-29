"""Public contracts for generic scientific analysis."""

from tru_ai.scientific.adapters import ScientificInputAdapter
from tru_ai.scientific.models import (
    ScientificAnalysisOptions,
    ScientificAnalysisRequest,
    ScientificAnalysisResult,
    ScientificBaselineInput,
    ScientificHumanReadable,
    ScientificPredictionRuleInput,
    ScientificStageCard,
    ScientificSummary,
    ScientificTheoryInput,
    ScientificTheoryRevisionRecommendation,
)
from tru_ai.scientific.service import ScientificService

__all__ = [
    "ScientificInputAdapter",
    "ScientificAnalysisOptions",
    "ScientificAnalysisRequest",
    "ScientificAnalysisResult",
    "ScientificBaselineInput",
    "ScientificHumanReadable",
    "ScientificPredictionRuleInput",
    "ScientificStageCard",
    "ScientificSummary",
    "ScientificTheoryInput",
    "ScientificTheoryRevisionRecommendation",
    "ScientificService",
]
