from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
)
from tru_ai.cognitive.reasoning.models import (
    ReasoningStage,
    ReasoningStep,
    TruthStatus,
)


class SynthesisEngine:
    """
    Produit une synthèse descriptive et vérifiable de l'exécution.

    La synthèse conserve le bilan épistémique historique. Lorsqu'une étape
    de réflexivité a effectivement produit des relations ou des boucles,
    elle ajoute un bilan réflexif séparé afin de ne pas confondre les faits,
    les déductions et les structures relationnelles détectées.
    """

    stage = ReasoningStage.SYNTHESIS

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        synthesis = self._build_synthesis(state)
        state.synthesis = synthesis

        return {
            "synthesis": synthesis,
            "reflexivity_summary": self._build_reflexivity_summary(state),
            "recognition_meaning_summary": (
                self._build_recognition_meaning_summary(state)
            ),
            "scientific_summary": self._build_scientific_summary(state),
            "reflexive_contradiction_summary": (
                self._build_reflexive_contradiction_summary(state)
            ),
        }

    @classmethod
    def _build_synthesis(
        cls,
        state: ReasoningExecutionState,
    ) -> str:
        explicit_count = len(
            state.claims_by_status(TruthStatus.EXPLICIT)
        )
        deduction_count = len(
            state.claims_by_status(TruthStatus.DEDUCTION)
        )
        hypothesis_count = len(
            state.claims_by_status(TruthStatus.HYPOTHESIS)
        )
        contradiction_count = len(state.contradictions)
        missing_count = len(state.missing_knowledge)

        epistemic_summary = (
            "Le raisonnement a identifié "
            f"{explicit_count} élément(s) explicite(s), "
            f"{deduction_count} déduction(s), "
            f"{hypothesis_count} hypothèse(s), "
            f"{contradiction_count} contradiction(s) et "
            f"{missing_count} connaissance(s) manquante(s)."
        )

        additions = [
            cls._build_reflexivity_summary(state),
            cls._build_recognition_meaning_summary(state),
            cls._build_scientific_summary(state),
            cls._build_reflexive_contradiction_summary(state),
        ]
        visible_additions = [
            addition
            for addition in additions
            if addition is not None
        ]

        if not visible_additions:
            return epistemic_summary

        return " ".join((epistemic_summary, *visible_additions))

    @staticmethod
    def _build_reflexivity_summary(
        state: ReasoningExecutionState,
    ) -> str | None:
        relation_count = len(state.reflexive_relations)
        loop_count = len(state.reflexive_loops)

        if relation_count == 0 and loop_count == 0:
            return None

        self_relation_count = sum(
            1
            for relation in state.reflexive_relations
            if relation.observer == relation.observed
        )
        loop_relation_count = sum(
            1
            for relation in state.reflexive_relations
            if relation.recognition_level == 2
        )

        return (
            "L'analyse réflexive a identifié "
            f"{relation_count} relation(s) réflexive(s), "
            f"{loop_count} boucle(s) fermée(s), "
            f"dont {self_relation_count} auto-relation(s) et "
            f"{loop_relation_count} relation(s) appartenant à une boucle."
        )



    @staticmethod
    def _build_recognition_meaning_summary(
        state: ReasoningExecutionState,
    ) -> str | None:
        graph = state.recognition_meaning_graph
        if not graph.meanings and not graph.gaps:
            return None

        return (
            "L'analyse de signification de la reconnaissance a décrit "
            f"{len(graph.meanings)} objet(s) reconnu(s), "
            f"{len(graph.gaps)} écart(s), avec une complétude structurelle "
            f"de {graph.completeness.score:.2f} et une stabilité de "
            f"{graph.stability.score:.2f}."
        )


    @staticmethod
    def _build_scientific_summary(
        state: ReasoningExecutionState,
    ) -> str | None:
        scientific_intents = {
            "scientific_research",
            "theory_construction",
            "theory_comparison",
            "theory_evolution",
            "prediction",
            "scientific_gaps",
        }
        scientific_context_keys = {
            "theory",
            "theory_graph",
            "baseline_theory",
            "comparison_theories",
            "predictions",
        }
        scientific_mode_requested = (
            state.intent in scientific_intents
            or any(
                key in state.conversation_context
                for key in scientific_context_keys
            )
        )

        if not scientific_mode_requested:
            return None

        graph = state.theory_graph
        if (
            not graph.claims
            and not state.theory_comparisons
            and not state.scientific_predictions
            and not state.scientific_gaps
        ):
            return None

        return (
            "Le moteur scientifique a structuré "
            f"{len(graph.claims)} proposition(s) théorique(s), comparé "
            f"{len(state.theory_comparisons)} théorie(s), décrit "
            f"{len(state.theory_evolution.added_claims)} ajout(s), produit "
            f"{len(state.scientific_predictions)} prédiction(s) explicite(s) et identifié "
            f"{len(state.scientific_gaps)} lacune(s) scientifique(s)."
        )

    @staticmethod
    def _build_reflexive_contradiction_summary(
        state: ReasoningExecutionState,
    ) -> str | None:
        explicit_prefix = "Contradiction réflexive explicite :"
        tension_prefix = "Tension réflexive potentielle :"

        explicit_count = sum(
            1
            for contradiction in state.contradictions
            if contradiction.startswith(explicit_prefix)
        )
        tension_count = sum(
            1
            for contradiction in state.contradictions
            if contradiction.startswith(tension_prefix)
        )

        if explicit_count == 0 and tension_count == 0:
            return None

        return (
            "L'analyse de cohérence réflexive a identifié "
            f"{explicit_count} contradiction(s) réflexive(s) explicite(s) "
            f"et {tension_count} tension(s) potentielle(s)."
        )
