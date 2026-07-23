from __future__ import annotations

import re

from tru_ai.extraction.lexical_normalizer import (
    LexicalNormalizer,
)


class RelationNormalizer:
    """Normalise les sujets, prédicats et objets."""

    LEADING_DETERMINERS = (
        "la",
        "le",
        "les",
        "un",
        "une",
        "des",
        "du",
        "de la",
        "de l'",
        "l'",
        "toute",
        "tout",
        "tous",
        "toutes",
        "chaque",
        "ce",
        "cet",
        "cette",
        "ces",
    )

    PREDICATE_ALIASES = {
        "est": "etre",
        "sont": "etre",
        "était": "etre",
        "etait": "etre",
        "devient": "devenir",
        "deviennent": "devenir",
        "observe": "observer",
        "observent": "observer",
        "propose": "proposer",
        "proposent": "proposer",
        "produit": "produire",
        "produisent": "produire",
        "transforme": "transformer",
        "transforment": "transformer",
        "compare": "comparer",
        "comparent": "comparer",
        "permet": "permettre",
        "permettent": "permettre",
        "crée": "creer",
        "cree": "creer",
        "créent": "creer",
        "creent": "creer",
        "contient": "contenir",
        "contiennent": "contenir",
        "exprime": "exprimer",
        "expriment": "exprimer",
        "détermine": "determiner",
        "determine": "determiner",
        "déterminent": "determiner",
        "determinent": "determiner",
        "influence": "influencer",
        "influencent": "influencer",
        "reconnaît": "reconnaitre",
        "reconnait": "reconnaitre",
        "reconnaissent": "reconnaitre",
        "manifeste": "manifester",
        "manifestent": "manifester",
        "génère": "generer",
        "genere": "generer",
        "génèrent": "generer",
        "generent": "generer",
        "implique": "impliquer",
        "impliquent": "impliquer",
        "nécessite": "necessiter",
        "necessite": "necessiter",
        "nécessitent": "necessiter",
        "necessitent": "necessiter",
        "résulte de": "resulter_de",
        "resulte de": "resulter_de",
        "dépend de": "dependre_de",
        "depend de": "dependre_de",
        "est capable de": "etre_capable_de",
        "sont capables de": "etre_capable_de",
        "permet de": "permettre",
        "conduit à": "conduire_a",
        "conduit a": "conduire_a",
        "mène à": "mener_a",
        "mene a": "mener_a",
    }

    def __init__(
        self,
        lexical_normalizer: LexicalNormalizer | None = None,
    ) -> None:
        self.lexical_normalizer = (
            lexical_normalizer
            or LexicalNormalizer()
        )

    def normalize_entity(
        self,
        value: str,
    ) -> str:
        normalized = self.lexical_normalizer.normalize(
            value
        )

        normalized = normalized.strip(
            " ,;:.!?\"'()[]{}"
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        normalized = self.remove_leading_determiner(
            normalized
        )

        return normalized.strip()

    def normalize_predicate(
        self,
        value: str,
    ) -> str:
        normalized = self.lexical_normalizer.normalize(
            value
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return self.PREDICATE_ALIASES.get(
            normalized,
            normalized.replace(" ", "_"),
        )

    def remove_leading_determiner(
        self,
        value: str,
    ) -> str:
        determiners = sorted(
            self.LEADING_DETERMINERS,
            key=len,
            reverse=True,
        )

        for determiner in determiners:
            prefix = f"{determiner} "

            if value.startswith(prefix):
                return value[len(prefix):]

            if determiner.endswith("'") and value.startswith(
                determiner
            ):
                return value[len(determiner):]

        return value