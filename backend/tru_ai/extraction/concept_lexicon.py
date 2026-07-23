from __future__ import annotations

from tru_ai.extraction.concept_models import (
    ConceptDefinition,
)
from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)


DEFAULT_CONCEPTS = (
    ConceptDefinition(
        concept_id="tru",
        preferred_label=(
            "Théorie de la Réflexivité Universelle"
        ),
        category="theory",
        aliases=(
            "Théorie de la Réflexivité Universelle",
            "TRU",
            "théorie réflexive universelle",
        ),
        description=(
            "Cadre théorique général de la reconnaissance "
            "réflexive."
        ),
    ),
    ConceptDefinition(
        concept_id="conscience",
        preferred_label="Conscience",
        category="fundamental_concept",
        aliases=(
            "conscience",
            "conscience universelle",
        ),
    ),
    ConceptDefinition(
        concept_id="reconnaissance",
        preferred_label="Reconnaissance",
        category="fundamental_concept",
        aliases=(
            "reconnaissance",
            "se reconnaître",
            "se reconnaitre",
            "reconnaître",
            "reconnaitre",
        ),
    ),
    ConceptDefinition(
        concept_id="reflexivite",
        preferred_label="Réflexivité",
        category="fundamental_concept",
        aliases=(
            "réflexivité",
            "reflexivite",
            "réflexif",
            "réflexive",
            "reflexif",
            "reflexive",
        ),
    ),
    ConceptDefinition(
        concept_id="observation",
        preferred_label="Observation",
        category="process",
        aliases=(
            "observation",
            "observer",
            "observe",
            "observateur",
        ),
    ),
    ConceptDefinition(
        concept_id="relation",
        preferred_label="Relation",
        category="fundamental_concept",
        aliases=(
            "relation",
            "relations",
            "relationnel",
            "relationnelle",
        ),
    ),
    ConceptDefinition(
        concept_id="transformation",
        preferred_label="Transformation",
        category="process",
        aliases=(
            "transformation",
            "transformer",
            "se transforme",
        ),
    ),
    ConceptDefinition(
        concept_id="delta",
        preferred_label="Delta",
        category="operator",
        aliases=(
            "delta",
            "opérateur delta",
            "operateur delta",
            "écart",
            "ecart",
        ),
    ),
    ConceptDefinition(
        concept_id="prediction",
        preferred_label="Prédiction",
        category="process",
        aliases=(
            "prédiction",
            "prediction",
            "prédire",
            "predire",
            "état prédit",
            "etat predit",
        ),
    ),
    ConceptDefinition(
        concept_id="etat",
        preferred_label="État",
        category="structural_concept",
        aliases=(
            "état",
            "etat",
            "état initial",
            "etat initial",
            "état attendu",
            "etat attendu",
        ),
    ),
    ConceptDefinition(
        concept_id="memoire",
        preferred_label="Mémoire",
        category="fundamental_concept",
        aliases=(
            "mémoire",
            "memoire",
            "mémorisation",
            "memorisation",
        ),
    ),
    ConceptDefinition(
        concept_id="temps",
        preferred_label="Temps",
        category="fundamental_concept",
        aliases=(
            "temps",
            "temporalité",
            "temporalite",
        ),
    ),
    ConceptDefinition(
        concept_id="information",
        preferred_label="Information",
        category="fundamental_concept",
        aliases=(
            "information",
            "informations",
        ),
    ),
    ConceptDefinition(
        concept_id="manifestation",
        preferred_label="Manifestation",
        category="process",
        aliases=(
            "manifestation",
            "manifester",
            "se manifeste",
        ),
    ),
    ConceptDefinition(
        concept_id="temoignage",
        preferred_label="Témoignage",
        category="process",
        aliases=(
            "témoignage",
            "temoignage",
            "témoigner",
            "temoigner",
        ),
    ),
    ConceptDefinition(
        concept_id="nomination",
        preferred_label="Nomination",
        category="process",
        aliases=(
            "nomination",
            "nommer",
            "se nommer",
        ),
    ),
    ConceptDefinition(
        concept_id="integration",
        preferred_label="Intégration",
        category="process",
        aliases=(
            "intégration",
            "integration",
            "intégrer",
            "integrer",
        ),
    ),
    ConceptDefinition(
        concept_id="reciprocite",
        preferred_label="Réciprocité",
        category="fundamental_concept",
        aliases=(
            "réciprocité",
            "reciprocite",
            "réciproque",
            "reciproque",
        ),
    ),
    ConceptDefinition(
        concept_id="solitude",
        preferred_label="Solitude",
        category="fundamental_concept",
        aliases=(
            "solitude",
            "isolement",
        ),
    ),
    ConceptDefinition(
        concept_id="presence",
        preferred_label="Présence",
        category="fundamental_concept",
        aliases=(
            "présence",
            "presence",
            "être présent",
            "etre present",
        ),
    ),
    ConceptDefinition(
        concept_id="realite",
        preferred_label="Réalité",
        category="fundamental_concept",
        aliases=(
            "réalité",
            "realite",
            "réel",
            "reel",
        ),
    ),
    ConceptDefinition(
        concept_id="ame",
        preferred_label="Âme",
        category="metaphysical_concept",
        aliases=(
            "âme",
            "ame",
        ),
    ),
    ConceptDefinition(
        concept_id="corps",
        preferred_label="Corps",
        category="biological_concept",
        aliases=(
            "corps",
            "organisme",
        ),
    ),
)


class ConceptLexicon:
    """Index déterministe des concepts et de leurs alias."""

    def __init__(
        self,
        concepts: tuple[
            ConceptDefinition,
            ...,
        ] = DEFAULT_CONCEPTS,
        normalizer: LexicalNormalizer | None = None,
    ) -> None:
        self.normalizer = (
            normalizer or LexicalNormalizer()
        )

        self._concepts = {
            concept.concept_id: concept
            for concept in concepts
        }

        self._aliases: dict[
            str,
            ConceptDefinition,
        ] = {}

        for concept in concepts:
            aliases = (
                concept.preferred_label,
                *concept.aliases,
            )

            for alias in aliases:
                normalized_alias = (
                    self.normalizer.normalize(alias)
                )

                existing = self._aliases.get(
                    normalized_alias
                )

                if (
                    existing is not None
                    and existing.concept_id
                    != concept.concept_id
                ):
                    raise ValueError(
                        "Alias ambigu détecté : "
                        f"{alias!r} appartient à "
                        f"{existing.concept_id!r} et "
                        f"{concept.concept_id!r}."
                    )

                self._aliases[
                    normalized_alias
                ] = concept

    def get(
        self,
        concept_id: str,
    ) -> ConceptDefinition | None:
        return self._concepts.get(concept_id)

    def all_concepts(
        self,
    ) -> list[ConceptDefinition]:
        return sorted(
            self._concepts.values(),
            key=lambda concept: concept.concept_id,
        )

    def aliases_by_length(
        self,
    ) -> list[
        tuple[str, ConceptDefinition]
    ]:
        return sorted(
            self._aliases.items(),
            key=lambda item: (
                -len(item[0]),
                item[0],
            ),
        )