from __future__ import annotations

from tru_ai.cognitive.models import (
    CognitiveAnswer,
    CognitiveClaim,
    CognitiveEvidence,
    OperatorApplication,
    TruOperator,
    deterministic_id,
)
from tru_ai.memory.models import MemoryElement, SourceDocument


class ResponseBuilder:
    def build_evidence(
        self,
        elements: tuple[MemoryElement, ...],
    ) -> tuple[CognitiveEvidence, ...]:
        evidence = []
        for element in elements:
            evidence.append(
                CognitiveEvidence(
                    evidence_id=deterministic_id(
                        "cognitive-evidence",
                        {"element_id": element.element_id},
                    ),
                    element_id=element.element_id,
                    element_type=element.element_type,
                    text=element.text,
                    source_id=element.source_id,
                    document_id=element.document_id,
                    page_numbers=element.page_numbers,
                    relevance=1.0,
                    extraction_confidence=element.extraction_confidence,
                    semantic_validation_status=element.semantic_validation_status,
                    semantic_justification=element.semantic_justification,
                    authority=self._authority(element.element_type),
                    conceptual_proximity=1.0 if element.concept_ids else 0.55,
                    directness=self._directness(element.element_type),
                    completeness=self._completeness(element.text),
                    context_loss_risk=self._context_loss_risk(element.text),
                )
            )
        return tuple(sorted(evidence, key=lambda item: item.evidence_id))

    def build_claim(
        self,
        *,
        classification: str,
        text: str,
        evidence_ids: tuple[str, ...],
        confidence: float,
        premises: tuple[str, ...] = (),
        rule: str | None = None,
        conclusion: str | None = None,
        limitations: tuple[str, ...] = (),
        validity_score: float | None = None,
    ) -> CognitiveClaim:
        return CognitiveClaim(
            claim_id=deterministic_id(
                "cognitive-claim",
                {
                    "classification": classification,
                    "evidence_ids": sorted(evidence_ids),
                    "text": text,
                },
            ),
            classification=classification,
            text=text,
            evidence_ids=tuple(sorted(evidence_ids)),
            confidence=max(0.0, min(1.0, confidence)),
            premises=tuple(sorted(premises)),
            rule=rule,
            conclusion=conclusion,
            limitations=tuple(sorted(limitations)),
            validity_score=validity_score,
        )

    def build_answer(
        self,
        *,
        question: str,
        intent: str,
        concepts: tuple[str, ...],
        evidence: tuple[CognitiveEvidence, ...],
        sources: tuple[SourceDocument, ...],
        operators: tuple[TruOperator, ...] = (),
        applications: tuple[OperatorApplication, ...] = (),
    ) -> CognitiveAnswer:
        warnings: list[str] = []
        missing: list[str] = []
        explicit: list[CognitiveClaim] = []
        deductions: list[CognitiveClaim] = []
        hypotheses: list[CognitiveClaim] = []
        unknowns: list[CognitiveClaim] = []
        source_records = tuple(
            source.to_dict()
            for source in sorted(sources, key=lambda item: item.source_id)
        )

        if not evidence:
            missing.append(
                "Aucun passage canonique ne soutient directement la réponse."
            )
            unknowns.append(
                self.build_claim(
                    classification="INCONNU",
                    text=(
                        "La mémoire actuelle ne permet pas d'établir une réponse fiable."
                    ),
                    evidence_ids=(),
                    confidence=0.0,
                )
            )
            summary = (
                "TRU-AI reconnaît la question, mais ne dispose pas encore de preuves suffisantes dans sa mémoire canonique."
            )
        else:
            definition_evidence = tuple(
                item for item in evidence if item.element_type == "Définition"
            )
            primary = definition_evidence or evidence[:2]
            for item in primary[:4]:
                explicit.append(
                    self.build_claim(
                        classification="EXPLICITE",
                        text=item.text,
                        evidence_ids=(item.evidence_id,),
                        confidence=(
                            0.92 if item.element_type == "Définition" else 0.78
                        ),
                    )
                )

            applied = tuple(
                application
                for application in applications
                if application.applied and application.output
            )
            for application in applied:
                deductions.append(
                    self.build_claim(
                        classification="DÉDUCTION",
                    text=(
                        f"Application de l'opérateur {application.operator_id} : {application.output}."
                    ),
                    evidence_ids=application.premise_evidence_ids,
                    confidence=application.confidence,
                    premises=application.premise_evidence_ids,
                    rule=application.rule,
                    conclusion=application.output,
                    limitations=(),
                    validity_score=application.confidence,
                )
            )

            refused = tuple(
                application
                for application in applications
                if not application.applied and application.refusal_reason
            )
            for application in refused:
                missing.append(application.refusal_reason or "")

            if intent == "applied_analysis":
                hypotheses.append(
                    self.build_claim(
                        classification="HYPOTHÈSE",
                        text=(
                            "L'application au burn-out est interprétative si le traité ne le nomme pas explicitement ; elle ne constitue pas un diagnostic médical."
                        ),
                        evidence_ids=tuple(item.evidence_id for item in evidence[:3]),
                        confidence=0.45,
                    )
                )
                warnings.append(
                    "Analyse conceptuelle uniquement ; aucun diagnostic médical n'est produit."
                )

            summary = self._summary(
                concepts=concepts,
                explicit=tuple(explicit),
                intent=intent,
                operators=operators,
            )

        return CognitiveAnswer(
            summary=summary,
            explicit_claims=tuple(explicit),
            deductions=tuple(deductions),
            hypotheses=tuple(hypotheses),
            unknowns=tuple(unknowns),
            sources=source_records,
            missing_knowledge=tuple(item for item in missing if item),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _summary(
        *,
        concepts: tuple[str, ...],
        explicit: tuple[CognitiveClaim, ...],
        intent: str,
        operators: tuple[TruOperator, ...],
    ) -> str:
        concept_text = ", ".join(concepts) if concepts else "la question"
        operator_text = (
            f" L'opérateur formalisé disponible est {operators[0].name}."
            if operators
            else ""
        )
        if intent == "applied_analysis":
            return (
                f"TRU-AI analyse {concept_text} en séparant les éléments explicitement soutenus, les déductions et les hypothèses.{operator_text}"
            )
        if explicit:
            return (
                f"TRU-AI explique {concept_text} à partir des formulations explicites disponibles et refuse l'application opératoire lorsque ses préconditions ne sont pas établies.{operator_text}"
            )
        return (
            f"TRU-AI ne dispose pas d'éléments explicites suffisants pour expliquer {concept_text}."
        )

    @staticmethod
    def _authority(element_type: str) -> float:
        return {
            "Définition": 0.95,
            "Axiome": 0.92,
            "Proposition": 0.86,
            "Démonstration": 0.84,
            "Observation": 0.72,
            "Exemple": 0.64,
            "Phrase": 0.5,
        }.get(element_type, 0.58)

    @staticmethod
    def _directness(element_type: str) -> float:
        return 0.95 if element_type in {"Définition", "Axiome"} else 0.72

    @staticmethod
    def _completeness(text: str) -> float:
        word_count = len(text.split())
        if 8 <= word_count <= 120:
            return 0.86
        if word_count < 8:
            return 0.52
        return 0.68

    @staticmethod
    def _context_loss_risk(text: str) -> float:
        word_count = len(text.split())
        if word_count < 8:
            return 0.55
        if word_count > 160:
            return 0.4
        return 0.18
