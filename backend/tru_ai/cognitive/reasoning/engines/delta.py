from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

from tru_ai.cognitive.reasoning.engines.base import (
    ReasoningExecutionState,
    normalize_string_sequence,
    normalize_text,
)
from tru_ai.cognitive.reasoning.models import (
    DeltaComparison,
    DeltaDirection,
    ReasoningStage,
    ReasoningStep,
)


class DeltaEngine:
    """
    Formalise l'écart entre un état de départ et un état prédit.

    Le moteur ne prédit aucun état. Il ne traite que les comparaisons
    explicitement fournies dans ``conversation_context["delta_comparisons"]``.
    Lorsqu'elles sont numériques, la valeur et la direction du Delta principal
    sont calculées. Les états désiré et observé restent optionnels et ne
    remplacent jamais l'état prédit dans le calcul principal.
    """

    stage = ReasoningStage.DELTA

    def execute(
        self,
        *,
        step: ReasoningStep,
        state: ReasoningExecutionState,
    ) -> Mapping[str, Any]:
        comparisons = self._normalize_comparisons(
            state.conversation_context.get("delta_comparisons", ())
        )
        state.delta_comparisons.extend(comparisons)
        return {
            "delta_comparisons": [item.to_dict() for item in comparisons],
        }

    def _normalize_comparisons(self, value: Any) -> list[DeltaComparison]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            return []

        result: list[DeltaComparison] = []
        seen_ids: set[str] = set()

        for index, item in enumerate(value, start=1):
            if not isinstance(item, Mapping):
                continue

            comparison_id = (
                normalize_text(item.get("comparison_id") or item.get("id"))
                or f"delta:{index}"
            )
            dimension = normalize_text(item.get("dimension")) or "unspecified"

            if comparison_id in seen_ids:
                continue
            if "start_state" not in item or "predicted_state" not in item:
                continue

            start_state = item["start_state"]
            predicted_state = item["predicted_state"]
            delta_value, direction = self._calculate_delta(
                start_state,
                predicted_state,
            )

            limitations = normalize_string_sequence(item.get("limitations", ()))
            if delta_value is None:
                limitations.append(
                    "Le Delta numérique ne peut pas être calculé à partir "
                    "des états fournis."
                )

            result.append(
                DeltaComparison(
                    comparison_id=comparison_id,
                    dimension=dimension,
                    start_state=start_state,
                    predicted_state=predicted_state,
                    desired_state=item.get("desired_state"),
                    observed_state=item.get("observed_state"),
                    delta_value=delta_value,
                    direction=direction,
                    evidence=tuple(
                        normalize_string_sequence(item.get("evidence", ()))
                    ),
                    limitations=tuple(dict.fromkeys(limitations)),
                )
            )
            seen_ids.add(comparison_id)

        return result

    @staticmethod
    def _calculate_delta(
        start_state: Any,
        predicted_state: Any,
    ) -> tuple[float | None, DeltaDirection]:
        if (
            isinstance(start_state, bool)
            or isinstance(predicted_state, bool)
            or not isinstance(start_state, Real)
            or not isinstance(predicted_state, Real)
        ):
            return None, DeltaDirection.UNDETERMINED

        value = float(predicted_state) - float(start_state)
        if value > 0:
            direction = DeltaDirection.INCREASE
        elif value < 0:
            direction = DeltaDirection.DECREASE
        else:
            direction = DeltaDirection.STABLE
        return value, direction
