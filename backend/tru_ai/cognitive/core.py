from __future__ import annotations

from tru_ai.cognitive.answer_planner import AnswerPlanner
from tru_ai.cognitive.concept_selector import ConceptSelector
from tru_ai.cognitive.intent import IntentDetector
from tru_ai.cognitive.memory_selector import MemorySelector
from tru_ai.cognitive.models import (
    CognitiveExecution,
    CognitiveRequestTrace,
    CognitiveResponse,
    deterministic_id,
)
from tru_ai.cognitive.operators import DeltaOperatorEngine
from tru_ai.cognitive.reasoning_orchestrator import ReasoningOrchestrator
from tru_ai.cognitive.response_builder import ResponseBuilder
from tru_ai.cognitive.self_evaluator import SelfEvaluator
from tru_ai.memory.models import CanonicalMemory, MemoryElement


class CognitiveCore:
    def __init__(self, memory: CanonicalMemory) -> None:
        self.memory = memory
        self.intent_detector = IntentDetector()
        self.concept_selector = ConceptSelector()
        self.memory_selector = MemorySelector()
        self.answer_planner = AnswerPlanner()
        self.reasoning_orchestrator = ReasoningOrchestrator()
        self.delta_engine = DeltaOperatorEngine()
        self.response_builder = ResponseBuilder()
        self.self_evaluator = SelfEvaluator()

    def ask(
        self,
        question: str,
        *,
        include_evidence: bool = True,
    ) -> CognitiveResponse:
        normalized_question = " ".join(question.strip().split())
        intent = self.intent_detector.detect(normalized_question)
        concepts = self.concept_selector.detect(
            normalized_question,
            self.memory,
        )
        problem = self._build_problem(
            question=normalized_question,
            intent=intent,
            concepts=concepts,
        )
        selected_elements = self.memory_selector.select_passages(
            question=normalized_question,
            concepts=concepts,
            memory=self.memory,
        )
        evidence = self.response_builder.build_evidence(selected_elements)
        comparison = self.delta_engine.compare(
            question=normalized_question,
            evidence=evidence,
        )
        delta_operator = self.delta_engine.formalize(evidence)
        delta_application = self.delta_engine.apply(
            operator=delta_operator,
            comparison=comparison,
        )
        operators = (delta_operator,) if delta_operator is not None else ()
        applications = (delta_application,)
        contradictions = self._detect_contradictions(evidence)
        source_ids = {item.source_id for item in selected_elements}
        sources = tuple(
            source
            for source in self.memory.sources
            if source.source_id in source_ids
        )
        answer = self.response_builder.build_answer(
            question=normalized_question,
            intent=intent,
            concepts=concepts,
            evidence=evidence,
            sources=sources,
            operators=operators,
            applications=applications,
        )
        confidence, justification = self.self_evaluator.evaluate(
            answer,
            production_source_count=len(
                [source for source in self.memory.sources if not source.is_demo_source]
            ),
            contradictions=contradictions,
            operator_applications=applications,
        )
        confidence_breakdown = self.self_evaluator.breakdown(
            answer,
            production_source_count=len(
                [source for source in self.memory.sources if not source.is_demo_source]
            ),
            contradictions=contradictions,
            operator_applications=applications,
        )
        if confidence == 0.0:
            confidence_breakdown = {
                **confidence_breakdown,
                "final_confidence": 0.0,
            }
        request_id = deterministic_id(
            "cognitive-request",
            {
                "question": normalized_question,
                "concepts": concepts,
                "evidence": [item.evidence_id for item in evidence],
                "intent": intent,
                "operators": [item.application_id for item in applications],
            },
        )
        response_plan = self.answer_planner.plan(intent)
        execution = self._execution(
            request_id=request_id,
            question=normalized_question,
            intent=intent,
            concepts=concepts,
            problem=problem,
            elements=selected_elements,
            evidence=evidence,
            comparison=comparison,
            operators=operators,
            applications=applications,
            contradictions=contradictions,
            answer=answer,
            response_plan=response_plan,
            confidence=confidence,
            confidence_justification=justification,
        )
        trace = self._trace(
            request_id=request_id,
            execution=execution,
            elements=selected_elements,
            answer=answer,
            evidence=evidence,
        )
        classifications = {
            "EXPLICITE": [claim.to_dict() for claim in answer.explicit_claims],
            "DÉDUCTION": [claim.to_dict() for claim in answer.deductions],
            "HYPOTHÈSE": [claim.to_dict() for claim in answer.hypotheses],
            "INCONNU": [claim.to_dict() for claim in answer.unknowns],
        }
        return CognitiveResponse(
            request_id=request_id,
            answer=answer,
            confidence=confidence,
            classifications=classifications,
            sources=answer.sources,
            missing_knowledge=answer.missing_knowledge,
            warnings=answer.warnings,
            trace=trace,
            evidence=evidence if include_evidence else (),
            execution=execution,
            confidence_breakdown=confidence_breakdown,
        )

    @staticmethod
    def _build_problem(
        *,
        question: str,
        intent: str,
        concepts: tuple[str, ...],
    ) -> str:
        concept_text = ", ".join(concepts) if concepts else "concepts non reconnus"
        return (
            f"Résoudre une demande de type {intent} portant sur {concept_text} à partir de preuves canoniques."
        )

    @staticmethod
    def _execution(
        *,
        request_id: str,
        question: str,
        intent: str,
        concepts: tuple[str, ...],
        problem: str,
        elements: tuple[MemoryElement, ...],
        evidence,
        comparison,
        operators,
        applications,
        contradictions: tuple[str, ...],
        answer,
        response_plan: tuple[str, ...],
        confidence: float,
        confidence_justification: str,
    ) -> CognitiveExecution:
        deductions = tuple(claim.claim_id for claim in answer.deductions)
        hypotheses = tuple(claim.claim_id for claim in answer.hypotheses)
        unknowns = tuple(claim.claim_id for claim in answer.unknowns)
        reflexive = {
            "question_understood": bool(question),
            "concepts_recognized": bool(concepts),
            "evidence_sufficient": bool(answer.explicit_claims),
            "unauthorized_rule_applied": False,
            "hypothesis_promoted_to_fact": False,
            "contradiction_detected": bool(contradictions),
            "confidence_matches_evidence": confidence > 0 or bool(unknowns),
            "missing_information_count": len(answer.missing_knowledge),
            "confidence_breakdown": dict(sorted(confidence_justification and {})),
        }
        return CognitiveExecution(
            execution_id=deterministic_id(
                "cognitive-execution",
                {
                    "request_id": request_id,
                    "evidence": [item.evidence_id for item in evidence],
                    "applications": [item.application_id for item in applications],
                },
            ),
            question=question,
            context=(),
            observation=f"Question observée : {question}",
            intention=intent,
            concepts_recognized=concepts,
            concepts_rejected=(),
            problem=problem,
            memory_activated=tuple(element.element_id for element in elements),
            evidence_selected=tuple(item.evidence_id for item in evidence),
            comparisons=(comparison,),
            deltas_detected=(
                (comparison.delta_detected,)
                if comparison.delta_detected is not None
                else ()
            ),
            applicable_operators=operators,
            applied_operators=applications,
            premises=tuple(item.evidence_id for item in evidence),
            rules=tuple(application.rule for application in applications),
            deductions=deductions,
            hypotheses=hypotheses,
            unknowns=unknowns,
            contradictions=contradictions,
            reflexive_evaluation=reflexive,
            response_plan=response_plan,
            final_answer=answer.summary,
            confidence=confidence,
            confidence_justification=confidence_justification,
        )

    @staticmethod
    def _detect_contradictions(evidence) -> tuple[str, ...]:
        if not evidence:
            return ()
        propositions: dict[tuple[str, str], set[str]] = {}
        for item in evidence:
            normalized = f" {item.text.lower()} "
            concept = None
            if "delta" in normalized:
                concept = "delta"
            elif "reconnaissance" in normalized:
                concept = "reconnaissance"
            elif "observation" in normalized:
                concept = "observation"
            if concept is None:
                continue
            property_name = None
            for marker in ("écart", "mesure", "transformation", "comparaison"):
                if marker in normalized:
                    property_name = marker
                    break
            if property_name is None:
                continue
            direct_negative = (
                f"{concept} n'est pas" in normalized
                or f"{concept} ne " in normalized
                and " pas " in normalized
                and normalized.index(f"{concept} ne ") < normalized.index(" pas ")
            )
            if "ne désigne plus seulement" in normalized:
                direct_negative = False
            if "ne mesure pas une erreur quantitative" in normalized:
                direct_negative = False
            if "n'est pas seulement" in normalized:
                direct_negative = False
            if "ne doit donc pas" in normalized or "ne doit pas" in normalized:
                direct_negative = False
            polarity = "negative" if direct_negative else "affirmative"
            propositions.setdefault((concept, property_name), set()).add(polarity)
        contradictions = []
        for (concept, property_name), polarities in sorted(propositions.items()):
            if {"affirmative", "negative"} <= polarities:
                contradictions.append(
                    f"Contradiction probable : {concept} porte une affirmation et une négation sur la propriété {property_name} dans des preuves comparables."
                )
        return tuple(contradictions)

    @staticmethod
    def _trace(
        *,
        request_id: str,
        execution: CognitiveExecution,
        elements: tuple[MemoryElement, ...],
        answer,
        evidence,
    ) -> CognitiveRequestTrace:
        pages = sorted(
            {page for element in elements for page in element.page_numbers}
        )
        definitions = tuple(
            element.element_id
            for element in elements
            if element.element_type == "Définition"
        )
        axioms = tuple(
            element.element_id
            for element in elements
            if element.element_type == "Axiome"
        )
        propositions = tuple(
            element.element_id
            for element in elements
            if element.element_type == "Proposition"
        )
        demonstrations = tuple(
            element.element_id
            for element in elements
            if element.element_type == "Démonstration"
        )
        chapters = tuple(
            element.element_id
            for element in elements
            if element.element_type == "Chapitre"
        )
        return CognitiveRequestTrace(
            request_id=request_id,
            original_question=execution.question,
            intent=execution.intention,
            detected_concepts=execution.concepts_recognized,
            selected_concepts=execution.concepts_recognized,
            sources_consulted=tuple(sorted({item.source_id for item in evidence})),
            pages_consulted=tuple(pages),
            chapters_consulted=chapters,
            definitions_used=definitions,
            axioms_used=axioms,
            propositions_used=propositions,
            demonstrations_used=demonstrations,
            relations_used=(),
            inferences_used=(),
            evidence_used=tuple(item.evidence_id for item in evidence),
            evidence_rejected=(),
            response_plan=execution.response_plan,
            explicit_claim_ids=tuple(
                claim.claim_id for claim in answer.explicit_claims
            ),
            deduction_claim_ids=tuple(claim.claim_id for claim in answer.deductions),
            hypothesis_claim_ids=tuple(
                claim.claim_id for claim in answer.hypotheses
            ),
            unknown_claim_ids=tuple(claim.claim_id for claim in answer.unknowns),
            contradictions=execution.contradictions,
            missing_knowledge=answer.missing_knowledge,
            coverage_score=1.0 if evidence else 0.0,
            confidence=execution.confidence,
            confidence_justification=execution.confidence_justification,
        )
