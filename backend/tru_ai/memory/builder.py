from __future__ import annotations

import re
from pathlib import Path

from tru_ai.extraction.concept_extractor import ConceptExtractor
from tru_ai.extraction.concept_lexicon import ConceptLexicon
from tru_ai.memory.importer import DocumentImporter, ExtractedBlock
from tru_ai.memory.models import (
    CanonicalMemory,
    MemoryBuildReport,
    MemoryElement,
    SourceDocument,
    stable_hash,
    stable_id,
)
from tru_ai.parsing.models import ParsedParagraph, ParsedSentence
from tru_ai.parsing.sentence_splitter import SentenceSplitter


DEFINITION_PATTERN = re.compile(
    r"\b(est défini comme|est définie comme|se définit comme|désigne|correspond à|peut être définie comme)\b",
    flags=re.IGNORECASE,
)
AXIOM_PATTERN = re.compile(r"\b(axiome|postulat)\b", flags=re.IGNORECASE)
PROPOSITION_PATTERN = re.compile(
    r"\b(proposition|thèse)\b",
    flags=re.IGNORECASE,
)
DEMONSTRATION_PATTERN = re.compile(
    r"\b(démonstration|preuve formelle|il s'ensuit|par conséquent|on peut donc déduire)\b",
    flags=re.IGNORECASE,
)
OBSERVATION_PATTERN = re.compile(
    r"\b(observation\s*:|observation fondamentale|on observe|est observé|est observée)\b",
    flags=re.IGNORECASE,
)
EXAMPLE_PATTERN = re.compile(
    r"\b(exemple|par exemple)\b",
    flags=re.IGNORECASE,
)
HYPOTHESIS_PATTERN = re.compile(
    r"\b(hypothèse|supposons|peut être interprété)\b",
    flags=re.IGNORECASE,
)
OPERATOR_PATTERN = re.compile(
    r"\b(opérateur\s+delta|delta\s+désigne|delta\s+mesure|appliquer\s+delta|application\s+de\s+delta|calcul\s+de\s+delta)\b",
    flags=re.IGNORECASE,
)
DELTA_CANDIDATE_PATTERN = re.compile(
    r"\b(delta|écart entre|comparaison|reconnaissance|transformation)\b",
    flags=re.IGNORECASE,
)


class CanonicalMemoryBuilder:
    def __init__(
        self,
        sources_directory: Path,
        *,
        demo_directory: Path | None = None,
    ) -> None:
        self.sources_directory = sources_directory
        self.demo_directory = demo_directory
        self.lexicon = ConceptLexicon()
        self.extractor = ConceptExtractor(self.lexicon)
        self.splitter = SentenceSplitter()

    def build(self) -> tuple[CanonicalMemory, MemoryBuildReport]:
        importer = DocumentImporter(self.sources_directory)
        source_paths = list(importer.discover())
        demo_paths: list[Path] = []
        if not source_paths and self.demo_directory is not None:
            demo_paths = list(DocumentImporter(self.demo_directory).discover())

        documents = [importer.import_path(path) for path in source_paths]
        if demo_paths:
            demo_importer = DocumentImporter(self.demo_directory)
            documents.extend(demo_importer.import_path(path) for path in demo_paths)

        sources: list[SourceDocument] = []
        elements: list[MemoryElement] = []
        order = 0

        for document in documents:
            is_demo = document.path in demo_paths
            source_id = stable_id(
                "source",
                {
                    "path": document.path.as_posix().lower(),
                    "hash": stable_hash(document.path.read_bytes().hex()),
                },
            )
            content = "\n".join(block.text for block in document.blocks)
            source = SourceDocument(
                source_id=source_id,
                path=str(document.path),
                format=document.format,
                title=document.title,
                byte_size=document.path.stat().st_size,
                content_hash=stable_hash(content),
                page_count=document.page_count,
                extracted_page_count=document.extracted_page_count,
                empty_page_numbers=document.empty_page_numbers,
                extraction_errors=document.extraction_errors,
                is_demo_source=is_demo,
            )
            sources.append(source)
            document_id = stable_id(
                "memory-document",
                {"source_id": source_id, "title": document.title},
            )
            doc_element = self._element(
                element_type="Document",
                text=document.title,
                order=order,
                position="document",
                parent_id=None,
                document_id=document_id,
                source_id=source_id,
                page_numbers=(),
                provenance={"source_path": str(document.path)},
                detection_method="source_document",
                extraction_confidence=1.0,
            )
            order += 1
            elements.append(doc_element)
            current_parent = doc_element.element_id

            for block in document.blocks:
                (
                    block_type,
                    parent,
                    detection_method,
                    extraction_confidence,
                ) = self._classify_block(block, current_parent)
                if block.block_type == "heading":
                    current_parent = None

                element = self._element(
                    element_type=block_type,
                    text=block.text,
                    order=order,
                    position=f"block-{block.order:05d}",
                    parent_id=parent,
                    document_id=document_id,
                    source_id=source_id,
                    page_numbers=(block.page_number,) if block.page_number else (),
                    provenance={
                        "source_path": str(document.path),
                        "block_order": str(block.order),
                        "page": str(block.page_number or ""),
                    },
                    detection_method=detection_method,
                    extraction_confidence=extraction_confidence,
                )
                order += 1
                elements.append(element)

                if block.block_type == "heading":
                    current_parent = element.element_id

                if block_type in {
                    "Paragraphe",
                    "Définition",
                    "Axiome",
                    "Proposition",
                    "Démonstration",
                    "Observation",
                    "Exemple",
                    "Hypothèse",
                    "Opérateur",
                }:
                    for sentence in self._sentences(element, block.text):
                        sentence_element = self._element(
                            element_type="Phrase",
                            text=sentence.content,
                            order=order,
                            position=(
                                f"{element.position}/sentence-"
                                f"{sentence.position:05d}"
                            ),
                            parent_id=element.element_id,
                            document_id=document_id,
                            source_id=source_id,
                            page_numbers=element.page_numbers,
                            provenance={
                                **element.provenance,
                                "sentence_id": sentence.sentence_id,
                            },
                            detection_method="sentence_splitter",
                            extraction_confidence=0.9,
                        )
                        order += 1
                        elements.append(sentence_element)

        elements = self._attach_children(elements)
        memory = CanonicalMemory(
            sources=tuple(sorted(sources, key=lambda item: item.source_id)),
            elements=tuple(
                sorted(elements, key=lambda item: (item.order, item.element_id))
            ),
        )
        report = self._report(memory)
        if not sources:
            report.add_error("Aucune source de traité trouvée dans corpus/sources.")
        elif report.production_source_count == 0:
            report.add_warning(
                "Aucune source de production trouvée ; seuls les fichiers de démonstration ont été utilisés."
            )
        if (
            report.production_source_count > 0
            and report.announced_pages > 10
            and report.extracted_words < 1000
        ):
            report.add_error(
                "Extraction manifestement incomplète pour une source de production."
            )
        return memory, report

    def _element(
        self,
        *,
        element_type: str,
        text: str,
        order: int,
        position: str,
        parent_id: str | None,
        document_id: str,
        source_id: str,
        page_numbers: tuple[int, ...],
        provenance: dict,
        detection_method: str = "deterministic_pattern",
        extraction_confidence: float = 0.75,
    ) -> MemoryElement:
        concept_ids = self._concepts_for_text(text)
        semantic_status, semantic_justification = self._semantic_quality(
            element_type,
            text,
            extraction_confidence,
        )
        operator_taxonomy = self._operator_taxonomy(element_type, text)
        element_id = stable_id(
            "memory-element",
            {
                "document_id": document_id,
                "order": order,
                "position": position,
                "text_hash": stable_hash(text),
                "type": element_type,
            },
        )
        return MemoryElement(
            element_id=element_id,
            element_type=element_type,
            text=text,
            order=order,
            position=position,
            parent_id=parent_id,
            child_ids=(),
            document_id=document_id,
            source_id=source_id,
            page_numbers=page_numbers,
            provenance=provenance,
            content_hash=stable_hash(text),
            concept_ids=tuple(concept_ids),
            detection_level=(
                "explicit_pattern"
                if extraction_confidence >= 0.9
                else "heuristic"
            ),
            detection_method=detection_method,
            extraction_confidence=extraction_confidence,
            semantic_validation_status=semantic_status,
            semantic_justification=semantic_justification,
            operator_taxonomy=operator_taxonomy,
        )

    def _classify_block(
        self,
        block: ExtractedBlock,
        current_parent: str,
    ) -> tuple[str, str | None, str, float]:
        text = block.text
        if block.block_type == "table":
            return "Tableau", current_parent, "doc_table", 0.95
        if block.block_type == "heading":
            lowered = text.lower()
            if lowered.startswith("volume"):
                return "Volume", None, "heading_pattern", 0.95
            if lowered.startswith("partie"):
                return "Partie", current_parent, "heading_pattern", 0.95
            if lowered.startswith("chapitre") or block.level == 1:
                return "Chapitre", None, "heading_pattern", 0.95
            if block.level == 2:
                return "Section", current_parent, "heading_pattern", 0.9
            return "Sous-section", current_parent, "heading_pattern", 0.85
        if AXIOM_PATTERN.search(text):
            return "Axiome", current_parent, "axiom_pattern", 0.92
        if PROPOSITION_PATTERN.search(text):
            return "Proposition", current_parent, "proposition_pattern", 0.88
        if DEFINITION_PATTERN.search(text):
            return "Définition", current_parent, "definition_pattern", 0.92
        if DEMONSTRATION_PATTERN.search(text):
            return "Démonstration", current_parent, "demonstration_pattern", 0.88
        if EXAMPLE_PATTERN.search(text):
            return "Exemple", current_parent, "example_pattern", 0.82
        if HYPOTHESIS_PATTERN.search(text):
            return "Hypothèse", current_parent, "hypothesis_pattern", 0.84
        if OPERATOR_PATTERN.search(text):
            return "Opérateur", current_parent, "operator_delta_pattern", 0.91
        if OBSERVATION_PATTERN.search(text):
            return "Observation", current_parent, "observation_pattern", 0.84
        return "Paragraphe", current_parent, "paragraph_default", 0.7

    @staticmethod
    def _semantic_quality(
        element_type: str,
        text: str,
        extraction_confidence: float,
    ) -> tuple[str, str]:
        lowered = text.lower()
        if element_type in {
            "Document",
            "Volume",
            "Partie",
            "Chapitre",
            "Section",
            "Sous-section",
            "Tableau",
            "Phrase",
        }:
            return "CONFIRMÉ", "Type issu de la structure documentaire ou de la segmentation déterministe."
        if element_type == "Paragraphe":
            return "PROBABLE", "Paragraphe retenu par défaut après exclusion des formes spécialisées."
        if element_type == "Définition" and DEFINITION_PATTERN.search(text):
            return "CONFIRMÉ", "Marqueur définitoire explicite détecté."
        if element_type == "Axiome" and re.search(r"\b(axiome|postulat)\b", lowered):
            return "CONFIRMÉ", "Marqueur axiome ou postulat détecté."
        if element_type == "Opérateur" and OPERATOR_PATTERN.search(text):
            return "CONFIRMÉ", "Delta est exprimé comme opérateur ou mesure d'écart."
        if element_type in {"Proposition", "Démonstration", "Exemple", "Hypothèse"}:
            return "PROBABLE", "Marqueur explicite détecté, mais la portée logique reste à vérifier."
        if element_type == "Observation":
            return "PROBABLE", "Marqueur d'observation structurée détecté."
        if extraction_confidence >= 0.8:
            return "PROBABLE", "Confiance d'extraction suffisante pour usage prudent."
        if DELTA_CANDIDATE_PATTERN.search(text):
            return "CANDIDAT", "Passage conceptuellement proche mais non validé comme connaissance forte."
        return "CANDIDAT", "Classification heuristique faible."

    @staticmethod
    def _operator_taxonomy(element_type: str, text: str) -> str | None:
        lowered = text.lower()
        if element_type == "Opérateur" and OPERATOR_PATTERN.search(text):
            return "operateur_tru_formalise" if "delta" in lowered else "operateur_tru_candidat"
        if DELTA_CANDIDATE_PATTERN.search(text):
            if "delta" in lowered:
                return "operateur_tru_candidat"
            if "comparaison" in lowered or "transformation" in lowered:
                return "processus_theorique"
            if "reconnaissance" in lowered or "observation" in lowered:
                return "operation_cognitive_generale"
        return None

    def _sentences(
        self,
        parent: MemoryElement,
        text: str,
    ) -> tuple[ParsedSentence, ...]:
        paragraph = ParsedParagraph(
            paragraph_id=parent.element_id,
            document_id=parent.document_id,
            section_id=parent.parent_id or parent.document_id,
            position=parent.order,
            content=text,
        )
        return tuple(self.splitter.split(paragraph))

    def _concepts_for_text(self, text: str) -> tuple[str, ...]:
        sentence = ParsedSentence(
            sentence_id="memory-temp",
            document_id="memory-temp",
            section_id="memory-temp",
            paragraph_id="memory-temp",
            position=0,
            content=text,
            word_count=len(text.split()),
        )
        return tuple(
            sorted(
                {
                    occurrence.concept_id
                    for occurrence in self.extractor.extract(sentence)
                }
            )
        )

    @staticmethod
    def _attach_children(elements: list[MemoryElement]) -> list[MemoryElement]:
        child_map: dict[str, list[str]] = {}
        for element in elements:
            if element.parent_id is not None:
                child_map.setdefault(element.parent_id, []).append(
                    element.element_id
                )
        return [
            MemoryElement(
                **{
                    **element.to_dict(),
                    "child_ids": tuple(
                        sorted(child_map.get(element.element_id, []))
                    ),
                    "page_numbers": tuple(element.page_numbers),
                    "concept_ids": tuple(element.concept_ids),
                    "related_element_ids": tuple(element.related_element_ids),
                    "provenance": element.provenance,
                    "detection_level": element.detection_level,
                    "detection_method": element.detection_method,
                    "extraction_confidence": element.extraction_confidence,
                    "semantic_validation_status": element.semantic_validation_status,
                    "semantic_justification": element.semantic_justification,
                    "operator_taxonomy": element.operator_taxonomy,
                }
            )
            for element in elements
        ]

    @staticmethod
    def _report(memory: CanonicalMemory) -> MemoryBuildReport:
        report = MemoryBuildReport()
        report.files_found = len(memory.sources)
        for source in memory.sources:
            report.formats[source.format] = report.formats.get(source.format, 0) + 1
            report.total_bytes += source.byte_size
            report.announced_pages += source.page_count
            report.extracted_pages += source.extracted_page_count
            report.empty_pages += len(source.empty_page_numbers)
            report.error_pages += len(source.extraction_errors)
            if source.is_demo_source:
                report.demo_source_count += 1
            else:
                report.production_source_count += 1
        for element in memory.elements:
            report.extracted_characters += len(element.text)
            report.extracted_words += len(element.text.split())
            report.concepts_detected += len(element.concept_ids)
            if element.semantic_validation_status == "CONFIRMÉ":
                report.confirmed_elements += 1
            elif element.semantic_validation_status == "PROBABLE":
                report.probable_elements += 1
            elif element.semantic_validation_status == "REJETÉ":
                report.rejected_elements += 1
            else:
                report.candidate_elements += 1
            if element.operator_taxonomy == "operateur_tru_formalise":
                report.executable_operator_count += 1
            elif element.operator_taxonomy == "operateur_tru_candidat":
                report.candidate_operator_count += 1
            elif element.operator_taxonomy:
                report.non_executable_operator_count += 1
            if element.element_type == "Volume":
                report.volumes_detected += 1
            elif element.element_type == "Partie":
                report.parts_detected += 1
            elif element.element_type == "Chapitre":
                report.chapters_detected += 1
            elif element.element_type == "Section":
                report.sections_detected += 1
            elif element.element_type == "Paragraphe":
                report.paragraphs_detected += 1
            elif element.element_type == "Phrase":
                report.sentences_detected += 1
            elif element.element_type == "Définition":
                report.definitions_detected += 1
            elif element.element_type == "Axiome":
                report.axioms_detected += 1
            elif element.element_type == "Proposition":
                report.propositions_detected += 1
            elif element.element_type == "Démonstration":
                report.demonstrations_detected += 1
            elif element.element_type == "Observation":
                report.observations_detected += 1
            elif element.element_type == "Exemple":
                report.examples_detected += 1
            elif element.element_type == "Hypothèse":
                report.hypotheses_detected += 1
            elif element.element_type == "Opérateur":
                report.operators_detected += 1
            elif element.element_type == "Référence":
                report.references_detected += 1
            elif element.element_type in {
                "Document",
                "Tableau",
                "Chapitre",
                "Section",
                "Sous-section",
                "Volume",
                "Partie",
            }:
                pass
            else:
                report.unclassified_elements += 1
        report.coverage_rate = (
            report.extracted_pages / report.announced_pages
            if report.announced_pages
            else (1.0 if report.extracted_words else 0.0)
        )
        (
            report.semantic_precision_estimates,
            report.semantic_sample_counts,
        ) = CanonicalMemoryBuilder._precision_estimates(memory)
        return report

    @staticmethod
    def _precision_estimates(memory: CanonicalMemory) -> tuple[dict[str, float], dict[str, int]]:
        estimates: dict[str, float] = {}
        sample_counts: dict[str, int] = {}
        categories = (
            "Définition",
            "Axiome",
            "Proposition",
            "Démonstration",
            "Observation",
            "Exemple",
            "Hypothèse",
            "Opérateur",
        )
        for category in categories:
            elements = sorted(
                (
                    element
                    for element in memory.elements
                    if element.element_type == category
                ),
                key=lambda item: item.element_id,
            )
            sample = elements[:30]
            sample_counts[category] = len(sample)
            if not sample:
                estimates[category] = 1.0
                continue
            accepted = len(
                [
                    element
                    for element in sample
                    if element.semantic_validation_status in {"CONFIRMÉ", "PROBABLE"}
                ]
            )
            estimates[category] = accepted / len(sample)
        return estimates, sample_counts
