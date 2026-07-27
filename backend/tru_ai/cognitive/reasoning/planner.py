from __future__ import annotations

from tru_ai.cognitive.reasoning.models import (
    ReasoningPlan,
    ReasoningRequest,
    ReasoningStage,
    ReasoningStep,
)
from tru_ai.cognitive.reasoning.policy import ReasoningPolicy


_STAGE_OBJECTIVES: dict[ReasoningStage, str] = {
    ReasoningStage.OBSERVATION: "Décrire précisément la demande sans ajouter d'interprétation.",
    ReasoningStage.CONTEXT: "Identifier les éléments pertinents du contexte conversationnel.",
    ReasoningStage.EXPLICIT_CLAIMS: "Isoler les propositions explicitement établies par les sources ou la mémoire disponible.",
    ReasoningStage.DEDUCTIONS: "Formuler uniquement les conséquences logiques soutenues par les éléments explicites.",
    ReasoningStage.HYPOTHESES: "Distinguer les explications possibles qui restent à vérifier.",
    ReasoningStage.RECOGNITION: "Construire un graphe à partir des relations explicites et y détecter les motifs sans inventer de relation.",
    ReasoningStage.DELTA: "Comparer explicitement l’état de départ à l’état prédit.",
    ReasoningStage.REFLEXIVITY: "Identifier les auto-relations, réciprocités et cycles fermés sans inventer de lien.",
    ReasoningStage.RECOGNITION_MEANING: "Décrire les objets reconnus, les écarts, la stabilité et la complétude.",
    ReasoningStage.THEORY_CONSTRUCTION: "Construire une représentation explicite de la théorie et de ses propositions.",
    ReasoningStage.THEORY_COMPARISON: "Comparer la théorie courante aux théories fournies sans inventer de similarité.",
    ReasoningStage.THEORY_EVOLUTION: "Décrire les ajouts, retraits et changements de soutien de la théorie.",
    ReasoningStage.PREDICTION: "Structurer les prédictions fournies et leurs conditions de falsification.",
    ReasoningStage.SCIENTIFIC_GAPS: "Identifier les preuves, données et expériences manquantes.",
    ReasoningStage.CONTRADICTIONS: "Rechercher les incompatibilités internes ou externes.",
    ReasoningStage.MISSING_KNOWLEDGE: "Identifier les informations nécessaires qui ne sont pas disponibles.",
    ReasoningStage.SYNTHESIS: "Produire une conclusion proportionnée aux éléments disponibles.",
}

_STAGE_INPUTS: dict[ReasoningStage, tuple[str, ...]] = {
    ReasoningStage.OBSERVATION: ("question",),
    ReasoningStage.CONTEXT: ("conversation_context",),
    ReasoningStage.EXPLICIT_CLAIMS: ("question", "conversation_context"),
    ReasoningStage.DEDUCTIONS: ("explicit_claims",),
    ReasoningStage.HYPOTHESES: ("explicit_claims", "deductions"),
    ReasoningStage.RECOGNITION: ("explicit_claims", "deductions", "hypotheses", "recognition_graph"),
    ReasoningStage.DELTA: ("delta_comparisons", "recognition_patterns"),
    ReasoningStage.REFLEXIVITY: ("recognition_graph", "recognition_patterns", "delta_comparisons"),
    ReasoningStage.RECOGNITION_MEANING: (
        "recognition_graph", "recognition_patterns", "delta_comparisons",
        "reflexive_graph", "reflexive_relations", "reflexive_loops",
    ),
    ReasoningStage.THEORY_CONSTRUCTION: (
        "explicit_claims", "deductions", "hypotheses", "recognition_meaning_graph", "theory",
    ),
    ReasoningStage.THEORY_COMPARISON: ("theory_graph", "comparison_theories"),
    ReasoningStage.THEORY_EVOLUTION: ("theory_graph", "baseline_theory"),
    ReasoningStage.PREDICTION: ("theory_graph", "predictions"),
    ReasoningStage.SCIENTIFIC_GAPS: ("theory_graph", "theory_comparisons", "scientific_predictions"),
    ReasoningStage.CONTRADICTIONS: (
        "explicit_claims", "deductions", "hypotheses", "recognition_patterns",
        "delta_comparisons", "reflexive_relations", "reflexive_loops",
        "recognition_meaning_graph", "recognition_meanings", "recognition_gaps",
        "theory_graph", "theory_comparisons",
    ),
    ReasoningStage.MISSING_KNOWLEDGE: (
        "explicit_claims", "deductions", "hypotheses", "recognition_patterns",
        "delta_comparisons", "reflexive_relations", "reflexive_loops",
        "contradictions", "scientific_gaps",
    ),
    ReasoningStage.SYNTHESIS: (
        "explicit_claims", "deductions", "hypotheses", "recognition_patterns",
        "delta_comparisons", "reflexive_relations", "reflexive_loops",
        "recognition_meaning_graph", "recognition_meanings", "recognition_gaps",
        "theory_graph", "theory_comparisons", "theory_evolution",
        "scientific_predictions", "scientific_gaps", "contradictions", "missing_knowledge",
    ),
}

_STAGE_OUTPUTS: dict[ReasoningStage, tuple[str, ...]] = {
    ReasoningStage.OBSERVATION: ("normalized_problem",),
    ReasoningStage.CONTEXT: ("relevant_context",),
    ReasoningStage.EXPLICIT_CLAIMS: ("explicit_claims",),
    ReasoningStage.DEDUCTIONS: ("deductions",),
    ReasoningStage.HYPOTHESES: ("hypotheses",),
    ReasoningStage.RECOGNITION: ("recognition_graph", "recognition_patterns"),
    ReasoningStage.DELTA: ("delta_comparisons",),
    ReasoningStage.REFLEXIVITY: ("reflexive_graph", "reflexive_relations", "reflexive_loops"),
    ReasoningStage.RECOGNITION_MEANING: (
        "recognition_meaning_graph", "recognition_meanings", "recognition_gaps",
        "recognition_completeness", "recognition_stability",
    ),
    ReasoningStage.THEORY_CONSTRUCTION: ("theory_graph",),
    ReasoningStage.THEORY_COMPARISON: ("theory_comparisons",),
    ReasoningStage.THEORY_EVOLUTION: ("theory_evolution",),
    ReasoningStage.PREDICTION: ("scientific_predictions",),
    ReasoningStage.SCIENTIFIC_GAPS: ("scientific_gaps",),
    ReasoningStage.CONTRADICTIONS: ("contradictions",),
    ReasoningStage.MISSING_KNOWLEDGE: ("missing_knowledge",),
    ReasoningStage.SYNTHESIS: ("synthesis",),
}


class ReasoningPlanner:
    def __init__(self, *, policy: ReasoningPolicy | None = None) -> None:
        self.policy = policy or ReasoningPolicy()

    def plan(self, request: ReasoningRequest) -> ReasoningPlan:
        question = request.normalized_question()
        if not question:
            raise ValueError("La question ne peut pas être vide.")
        intent = str(request.intent or "").strip()
        if not intent:
            raise ValueError("L'intention ne peut pas être vide.")
        stages = self.policy.stages_for_intent(intent)
        steps = tuple(self._build_step(position, stage) for position, stage in enumerate(stages, start=1))
        return ReasoningPlan(
            question=question,
            intent=intent,
            steps=steps,
            policy_version=self.policy.version,
        )

    @staticmethod
    def _build_step(position: int, stage: ReasoningStage) -> ReasoningStep:
        return ReasoningStep(
            position=position,
            stage=stage,
            objective=_STAGE_OBJECTIVES[stage],
            inputs=_STAGE_INPUTS[stage],
            outputs=_STAGE_OUTPUTS[stage],
        )
