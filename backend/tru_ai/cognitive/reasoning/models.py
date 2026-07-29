from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ReasoningStage(StrEnum):
    """
    Étapes normalisées d'un raisonnement réflexif.
    """

    OBSERVATION = "observation"
    CONTEXT = "context"
    EXPLICIT_CLAIMS = "explicit_claims"
    DEDUCTIONS = "deductions"
    HYPOTHESES = "hypotheses"
    RECOGNITION = "recognition"
    DELTA = "delta"
    REFLEXIVITY = "reflexivity"
    RECOGNITION_MEANING = "recognition_meaning"
    THEORY_CONSTRUCTION = "theory_construction"
    THEORY_COMPARISON = "theory_comparison"
    THEORY_EVOLUTION = "theory_evolution"
    PREDICTION = "prediction"
    VERIFICATION = "verification"
    FALSIFICATION = "falsification"
    SCIENTIFIC_GAPS = "scientific_gaps"
    CONTRADICTIONS = "contradictions"
    MISSING_KNOWLEDGE = "missing_knowledge"
    SYNTHESIS = "synthesis"


class TruthStatus(StrEnum):
    """
    Statut épistémique attribuable à une proposition.
    """

    EXPLICIT = "EXPLICITE"
    DEDUCTION = "DÉDUCTION"
    HYPOTHESIS = "HYPOTHÈSE"
    UNKNOWN = "INCONNU"


class DeltaDirection(StrEnum):
    """Direction d'un écart numérique explicitement calculable."""

    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"
    UNDETERMINED = "undetermined"


class RecognitionPatternType(StrEnum):
    """
    Motifs relationnels observables par le moteur de reconnaissance.
    """

    REPETITION = "repetition"
    SYMMETRY = "symmetry"
    INVERSION = "inversion"
    FIXED_POINT = "fixed_point"
    TRANSFORMATION = "transformation"
    CYCLE = "cycle"
    BIFURCATION = "bifurcation"


class RecognitionGapType(StrEnum):
    """Types d'écarts de reconnaissance explicitement observables."""

    STRUCTURAL = "structural"
    EXPLICIT_UNRECOGNIZED = "explicit_unrecognized"
    SEARCHED = "searched"
    AVOIDED = "avoided"


@dataclass(frozen=True)
class ReasoningRequest:
    """
    Entrée minimale du moteur de raisonnement réflexif.
    """

    question: str
    intent: str
    conversation_context: dict[str, Any] = field(default_factory=dict)

    def normalized_question(self) -> str:
        return " ".join(str(self.question or "").strip().split())


@dataclass(frozen=True)
class ReasoningStep:
    """
    Une étape ordonnée du plan de raisonnement.
    """

    position: int
    stage: ReasoningStage
    objective: str
    required: bool = True
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stage"] = self.stage.value
        payload["inputs"] = list(self.inputs)
        payload["outputs"] = list(self.outputs)
        return payload


@dataclass(frozen=True)
class ReasoningPlan:
    """
    Plan déterministe produit avant l'exécution cognitive.
    """

    question: str
    intent: str
    steps: tuple[ReasoningStep, ...]
    policy_version: str = "tru-reasoning-v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "intent": self.intent,
            "policy_version": self.policy_version,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(frozen=True)
class ReasoningClaim:
    """
    Proposition produite ou examinée pendant le raisonnement.
    """

    text: str
    status: TruthStatus
    support: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "status": self.status.value,
            "support": list(self.support),
            "limitations": list(self.limitations),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RecognitionNode:
    """
    Élément explicitement présent dans le graphe de reconnaissance.
    """

    node_id: str
    label: str
    kind: str = "concept"
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "kind": self.kind,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class RecognitionRelation:
    """
    Relation explicitement déclarée entre deux nœuds.
    """

    relation_id: str
    source_id: str
    target_id: str
    relation_type: str = "related_to"
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class RecognitionGraph:
    """
    Graphe relationnel minimal utilisé par RecognitionEngine.
    """

    nodes: tuple[RecognitionNode, ...] = ()
    relations: tuple[RecognitionRelation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "relations": [relation.to_dict() for relation in self.relations],
        }


@dataclass(frozen=True)
class RecognitionPattern:
    """
    Motif détecté à partir de relations explicites et vérifiables.
    """

    pattern_type: RecognitionPatternType
    description: str
    evidence: tuple[str, ...] = ()
    node_ids: tuple[str, ...] = ()
    relation_ids: tuple[str, ...] = ()
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "evidence": list(self.evidence),
            "node_ids": list(self.node_ids),
            "relation_ids": list(self.relation_ids),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class DeltaComparison:
    """
    Comparaison explicite entre un état de départ et un état prédit.

    Le Delta principal porte sur ``start_state -> predicted_state``.
    Les états désiré et observé restent optionnels et sont conservés comme
    écarts secondaires, sans être confondus avec le Delta principal.
    """

    comparison_id: str
    dimension: str
    start_state: Any
    predicted_state: Any
    desired_state: Any | None = None
    observed_state: Any | None = None
    delta_value: float | None = None
    direction: DeltaDirection = DeltaDirection.UNDETERMINED
    evidence: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "dimension": self.dimension,
            "start_state": self.start_state,
            "predicted_state": self.predicted_state,
            "desired_state": self.desired_state,
            "observed_state": self.observed_state,
            "delta_value": self.delta_value,
            "direction": self.direction.value,
            "evidence": list(self.evidence),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ReflexiveRelation:
    """
    Relation réflexive explicite entre un observateur et un objet observé.

    Cette structure décrit uniquement une relation fournie ou construite
    explicitement. Elle n'infère aucune réflexivité par elle-même.
    """

    observer: str
    observed: str
    relation: str
    recognition_level: int
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "observer": self.observer,
            "observed": self.observed,
            "relation": self.relation,
            "recognition_level": self.recognition_level,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ReflexiveLoop:
    """
    Ensemble ordonné de relations réflexives formant éventuellement une boucle.
    """

    relations: tuple[ReflexiveRelation, ...] = ()
    closed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "relations": [relation.to_dict() for relation in self.relations],
            "closed": self.closed,
        }


@dataclass(frozen=True)
class ReflexiveGraph:
    """
    Graphe minimal regroupant les relations et les boucles réflexives.
    """

    relations: tuple[ReflexiveRelation, ...] = ()
    loops: tuple[ReflexiveLoop, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "relations": [relation.to_dict() for relation in self.relations],
            "loops": [loop.to_dict() for loop in self.loops],
        }


@dataclass(frozen=True)
class RecognitionMeaning:
    """Objet de reconnaissance décrit à partir de relations explicites."""

    object_id: str
    observers: tuple[str, ...] = ()
    relation_types: tuple[str, ...] = ()
    recognition_level: int = 0
    reciprocal: bool = False
    stable: bool = False
    evidence_relation_ids: tuple[str, ...] = ()
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "observers": list(self.observers),
            "relation_types": list(self.relation_types),
            "recognition_level": self.recognition_level,
            "reciprocal": self.reciprocal,
            "stable": self.stable,
            "evidence_relation_ids": list(self.evidence_relation_ids),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RecognitionGap:
    """Écart explicitement déclaré ou structurellement observable."""

    object_id: str
    gap_type: RecognitionGapType
    description: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "gap_type": self.gap_type.value,
            "description": self.description,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class RecognitionCompleteness:
    """Couverture structurelle des objets éligibles à la reconnaissance."""

    recognized_objects: int = 0
    total_objects: int = 0
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecognitionStability:
    """Stabilité structurelle des objets effectivement reconnus."""

    stable_objects: int = 0
    total_recognized_objects: int = 0
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecognitionMeaningGraph:
    """Résultat consolidé du calcul de signification de reconnaissance."""

    meanings: tuple[RecognitionMeaning, ...] = ()
    gaps: tuple[RecognitionGap, ...] = ()
    completeness: RecognitionCompleteness = field(
        default_factory=RecognitionCompleteness
    )
    stability: RecognitionStability = field(
        default_factory=RecognitionStability
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "meanings": [meaning.to_dict() for meaning in self.meanings],
            "gaps": [gap.to_dict() for gap in self.gaps],
            "completeness": self.completeness.to_dict(),
            "stability": self.stability.to_dict(),
        }



class TheoryClaimStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


@dataclass(frozen=True)
class TheoryClaim:
    claim_id: str
    text: str
    status: TheoryClaimStatus = TheoryClaimStatus.UNSUPPORTED
    evidence: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id, "text": self.text,
            "status": self.status.value, "evidence": list(self.evidence),
            "limitations": list(self.limitations), "confidence": self.confidence,
        }


@dataclass(frozen=True)
class TheoryGraph:
    theory_id: str = "current-theory"
    name: str = "Théorie courante"
    claims: tuple[TheoryClaim, ...] = ()
    relations: tuple[tuple[str, str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "theory_id": self.theory_id, "name": self.name,
            "claims": [claim.to_dict() for claim in self.claims],
            "relations": [list(relation) for relation in self.relations],
        }




class TheoryPropositionRole(StrEnum):
    AXIOM = "axiom"
    PROPOSITION = "proposition"
    HYPOTHESIS = "hypothesis"


@dataclass(frozen=True)
class TheoryEvidence:
    evidence_id: str
    description: str
    source: str | None = None
    strength: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TheoryProposition:
    proposition_id: str
    text: str
    role: TheoryPropositionRole = TheoryPropositionRole.PROPOSITION
    status: TheoryClaimStatus = TheoryClaimStatus.UNSUPPORTED
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    confidence: float = 0.0
    source_claim_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposition_id": self.proposition_id,
            "text": self.text,
            "role": self.role.value,
            "status": self.status.value,
            "evidence_ids": list(self.evidence_ids),
            "limitations": list(self.limitations),
            "confidence": self.confidence,
            "source_claim_ids": list(self.source_claim_ids),
        }


@dataclass(frozen=True)
class TheoryRevision:
    revision_id: str
    action: str
    proposition_id: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TheoryMaturity:
    score: float = 0.0
    level: str = "embryonic"
    supported_ratio: float = 0.0
    evidence_coverage: float = 0.0
    contradiction_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Theory:
    theory_id: str = "current-theory"
    title: str = "Théorie courante"
    domain: str | None = None
    propositions: tuple[TheoryProposition, ...] = ()
    evidence: tuple[TheoryEvidence, ...] = ()
    revisions: tuple[TheoryRevision, ...] = ()
    contradictions: tuple[str, ...] = ()
    maturity: TheoryMaturity = field(default_factory=TheoryMaturity)

    @property
    def axioms(self) -> tuple[TheoryProposition, ...]:
        return tuple(p for p in self.propositions if p.role is TheoryPropositionRole.AXIOM)

    @property
    def hypotheses(self) -> tuple[TheoryProposition, ...]:
        return tuple(p for p in self.propositions if p.role is TheoryPropositionRole.HYPOTHESIS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "theory_id": self.theory_id,
            "title": self.title,
            "domain": self.domain,
            "propositions": [p.to_dict() for p in self.propositions],
            "axioms": [p.to_dict() for p in self.axioms],
            "hypotheses": [p.to_dict() for p in self.hypotheses],
            "evidence": [e.to_dict() for e in self.evidence],
            "revisions": [r.to_dict() for r in self.revisions],
            "contradictions": list(self.contradictions),
            "maturity": self.maturity.to_dict(),
        }


@dataclass(frozen=True)
class TheoryComparison:
    compared_theory_id: str
    compared_theory_name: str
    shared_claims: tuple[str, ...] = ()
    current_only_claims: tuple[str, ...] = ()
    compared_only_claims: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "compared_theory_id": self.compared_theory_id,
            "compared_theory_name": self.compared_theory_name,
            "shared_claims": list(self.shared_claims),
            "current_only_claims": list(self.current_only_claims),
            "compared_only_claims": list(self.compared_only_claims),
            "contradictions": list(self.contradictions),
        }


@dataclass(frozen=True)
class TheoryEvolution:
    added_claims: tuple[str, ...] = ()
    removed_claims: tuple[str, ...] = ()
    strengthened_claims: tuple[str, ...] = ()
    weakened_claims: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {key: list(value) for key, value in asdict(self).items()}


class OperatorStatus(StrEnum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class OperatorTrace:
    operator: str
    stage: ReasoningStage
    position: int
    status: OperatorStatus = OperatorStatus.SUCCESS
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "stage": self.stage.value,
            "position": self.position,
            "status": self.status.value,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "error": self.error,
        }


@dataclass(frozen=True)
class TheorySnapshot:
    snapshot_id: str
    theory_id: str
    version: str
    propositions: tuple[TheoryProposition, ...] = ()
    maturity: TheoryMaturity = field(default_factory=TheoryMaturity)
    parent_snapshot_id: str | None = None
    change_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "theory_id": self.theory_id,
            "version": self.version,
            "propositions": [item.to_dict() for item in self.propositions],
            "maturity": self.maturity.to_dict(),
            "parent_snapshot_id": self.parent_snapshot_id,
            "change_summary": self.change_summary,
        }


@dataclass(frozen=True)
class TheoryHistory:
    theory_id: str
    snapshots: tuple[TheorySnapshot, ...] = ()
    current_snapshot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "theory_id": self.theory_id,
            "snapshots": [item.to_dict() for item in self.snapshots],
            "current_snapshot_id": self.current_snapshot_id,
        }


class PredictionConfidenceLevel(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True)
class ScientificPrediction:
    prediction_id: str
    text: str
    source_claim_ids: tuple[str, ...] = ()
    falsification_condition: str | None = None
    status: str = "untested"
    confidence: float = 0.0
    confidence_level: PredictionConfidenceLevel = PredictionConfidenceLevel.VERY_LOW
    confidence_factors: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    expected_observation: str | None = None
    horizon: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "text": self.text,
            "source_claim_ids": list(self.source_claim_ids),
            "falsification_condition": self.falsification_condition,
            "status": self.status,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "confidence_factors": list(self.confidence_factors),
            "assumptions": list(self.assumptions),
            "expected_observation": self.expected_observation,
            "horizon": self.horizon,
        }


@dataclass(frozen=True)
class ScientificScenario:
    scenario_id: str
    name: str
    description: str = ""
    assumptions: tuple[str, ...] = ()
    variables: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "assumptions": list(self.assumptions),
            "variables": dict(self.variables),
        }


@dataclass(frozen=True)
class ScenarioSimulation:
    simulation_id: str
    scenario_id: str
    prediction_id: str
    outcome: str
    adjusted_confidence: float
    matched_assumptions: tuple[str, ...] = ()
    missing_assumptions: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "scenario_id": self.scenario_id,
            "prediction_id": self.prediction_id,
            "outcome": self.outcome,
            "adjusted_confidence": self.adjusted_confidence,
            "matched_assumptions": list(self.matched_assumptions),
            "missing_assumptions": list(self.missing_assumptions),
            "rationale": self.rationale,
        }



class VerificationStatus(StrEnum):
    UNTESTED = "untested"
    CONFIRMED = "confirmed"
    WEAKENED = "weakened"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class ScientificObservation:
    observation_id: str
    text: str
    prediction_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    compatibility_score: float | None = None
    matches_falsification_condition: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "text": self.text,
            "prediction_id": self.prediction_id,
            "evidence_ids": list(self.evidence_ids),
            "compatibility_score": self.compatibility_score,
            "matches_falsification_condition": self.matches_falsification_condition,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class VerificationReport:
    report_id: str
    prediction_id: str
    observation_ids: tuple[str, ...] = ()
    status: VerificationStatus = VerificationStatus.UNTESTED
    consistency_score: float = 0.0
    evidence_score: float = 0.0
    rationale: str = ""
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "prediction_id": self.prediction_id,
            "observation_ids": list(self.observation_ids),
            "status": self.status.value,
            "consistency_score": self.consistency_score,
            "evidence_score": self.evidence_score,
            "rationale": self.rationale,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class FalsificationReport:
    report_id: str
    prediction_id: str
    verification_report_id: str
    falsified: bool = False
    formal_test_possible: bool = False
    falsification_condition_met: bool = False
    revision_required: bool = False
    affected_claim_ids: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "prediction_id": self.prediction_id,
            "verification_report_id": self.verification_report_id,
            "falsified": self.falsified,
            "formal_test_possible": self.formal_test_possible,
            "falsification_condition_met": self.falsification_condition_met,
            "revision_required": self.revision_required,
            "affected_claim_ids": list(self.affected_claim_ids),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ScientificTheoryRevision:
    revision_id: str
    prediction_id: str
    action: str
    affected_claim_ids: tuple[str, ...] = ()
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "prediction_id": self.prediction_id,
            "action": self.action,
            "affected_claim_ids": list(self.affected_claim_ids),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ScientificGap:
    gap_id: str
    description: str
    gap_type: str = "missing_evidence"
    related_claim_ids: tuple[str, ...] = ()
    required_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id, "description": self.description,
            "gap_type": self.gap_type,
            "related_claim_ids": list(self.related_claim_ids),
            "required_action": self.required_action,
        }


@dataclass(frozen=True)
class ReasoningResult:
    """
    Résultat structuré d'une exécution du plan.
    """

    plan: ReasoningPlan
    claims: tuple[ReasoningClaim, ...] = ()
    recognition_graph: RecognitionGraph = field(
        default_factory=RecognitionGraph
    )
    recognition_patterns: tuple[RecognitionPattern, ...] = ()
    delta_comparisons: tuple[DeltaComparison, ...] = ()
    reflexive_graph: ReflexiveGraph = field(
        default_factory=ReflexiveGraph
    )
    reflexive_relations: tuple[ReflexiveRelation, ...] = ()
    reflexive_loops: tuple[ReflexiveLoop, ...] = ()
    recognition_meaning_graph: RecognitionMeaningGraph = field(
        default_factory=RecognitionMeaningGraph
    )
    recognition_meanings: tuple[RecognitionMeaning, ...] = ()
    recognition_gaps: tuple[RecognitionGap, ...] = ()
    theory_graph: TheoryGraph = field(default_factory=TheoryGraph)
    theory: Theory = field(default_factory=Theory)
    theory_comparisons: tuple[TheoryComparison, ...] = ()
    theory_evolution: TheoryEvolution = field(default_factory=TheoryEvolution)
    theory_history: TheoryHistory = field(default_factory=lambda: TheoryHistory(theory_id="current-theory"))
    operator_trace: tuple[OperatorTrace, ...] = ()
    scientific_predictions: tuple[ScientificPrediction, ...] = ()
    scientific_scenarios: tuple[ScientificScenario, ...] = ()
    scenario_simulations: tuple[ScenarioSimulation, ...] = ()
    scientific_observations: tuple[ScientificObservation, ...] = ()
    verification_reports: tuple[VerificationReport, ...] = ()
    falsification_reports: tuple[FalsificationReport, ...] = ()
    scientific_theory_revisions: tuple[ScientificTheoryRevision, ...] = ()
    scientific_gaps: tuple[ScientificGap, ...] = ()
    contradictions: tuple[str, ...] = ()
    missing_knowledge: tuple[str, ...] = ()
    synthesis: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "claims": [claim.to_dict() for claim in self.claims],
            "recognition_graph": self.recognition_graph.to_dict(),
            "recognition_patterns": [
                pattern.to_dict()
                for pattern in self.recognition_patterns
            ],
            "delta_comparisons": [
                comparison.to_dict()
                for comparison in self.delta_comparisons
            ],
            "reflexive_graph": self.reflexive_graph.to_dict(),
            "reflexive_relations": [
                relation.to_dict()
                for relation in self.reflexive_relations
            ],
            "reflexive_loops": [
                loop.to_dict()
                for loop in self.reflexive_loops
            ],
            "recognition_meaning_graph": (
                self.recognition_meaning_graph.to_dict()
            ),
            "recognition_meanings": [
                meaning.to_dict() for meaning in self.recognition_meanings
            ],
            "recognition_gaps": [
                gap.to_dict() for gap in self.recognition_gaps
            ],
            "theory_graph": self.theory_graph.to_dict(),
            "theory": self.theory.to_dict(),
            "theory_comparisons": [item.to_dict() for item in self.theory_comparisons],
            "theory_evolution": self.theory_evolution.to_dict(),
            "theory_history": self.theory_history.to_dict(),
            "operator_trace": [item.to_dict() for item in self.operator_trace],
            "scientific_predictions": [item.to_dict() for item in self.scientific_predictions],
            "scientific_scenarios": [item.to_dict() for item in self.scientific_scenarios],
            "scenario_simulations": [item.to_dict() for item in self.scenario_simulations],
            "scientific_observations": [item.to_dict() for item in self.scientific_observations],
            "verification_reports": [item.to_dict() for item in self.verification_reports],
            "falsification_reports": [item.to_dict() for item in self.falsification_reports],
            "scientific_theory_revisions": [item.to_dict() for item in self.scientific_theory_revisions],
            "scientific_gaps": [item.to_dict() for item in self.scientific_gaps],
            "contradictions": list(self.contradictions),
            "missing_knowledge": list(self.missing_knowledge),
            "synthesis": self.synthesis,
        }