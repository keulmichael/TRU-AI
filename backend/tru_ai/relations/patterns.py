from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RelationPattern:
    pattern_id: str
    expression: re.Pattern[str]
    confidence: float
    predicate_override: str | None = None


SUBJECT = (
    r"(?P<subject>"
    r"[A-ZÀ-ÖØ-Ý0-9]"
    r"[^.!?;,:]{0,160}?"
    r")"
)

OBJECT = (
    r"(?P<object>"
    r"[^.!?;]{1,200}?"
    r")"
)


RELATION_PATTERNS = (
    RelationPattern(
        pattern_id="capable_de",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"est\s+capable\s+d['’]|"
            r"est\s+capable\s+de|"
            r"sont\s+capables\s+d['’]|"
            r"sont\s+capables\s+de"
            r")\s*"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.96,
        predicate_override="etre_capable_de",
    ),
    RelationPattern(
        pattern_id="permet_de",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"permet\s+de|"
            r"permettent\s+de"
            r")\s+"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.95,
        predicate_override="permettre",
    ),
    RelationPattern(
        pattern_id="depend_de",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"dépend\s+de|"
            r"depend\s+de"
            r")\s+"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.95,
        predicate_override="dependre_de",
    ),
    RelationPattern(
        pattern_id="resulte_de",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"résulte\s+de|"
            r"resulte\s+de"
            r")\s+"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.95,
        predicate_override="resulter_de",
    ),
    RelationPattern(
        pattern_id="conduit_a",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"conduit\s+à|"
            r"conduit\s+a|"
            r"mène\s+à|"
            r"mene\s+a"
            r")\s+"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.94,
    ),
    RelationPattern(
        pattern_id="transitive_verb",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"propose|"
            r"proposent|"
            r"observe|"
            r"observent|"
            r"produit|"
            r"produisent|"
            r"transforme|"
            r"transforment|"
            r"compare|"
            r"comparent|"
            r"permet|"
            r"permettent|"
            r"crée|"
            r"cree|"
            r"créent|"
            r"creent|"
            r"contient|"
            r"contiennent|"
            r"exprime|"
            r"expriment|"
            r"détermine|"
            r"determine|"
            r"déterminent|"
            r"determinent|"
            r"influence|"
            r"influencent|"
            r"reconnaît|"
            r"reconnait|"
            r"reconnaissent|"
            r"manifeste|"
            r"manifestent|"
            r"génère|"
            r"genere|"
            r"génèrent|"
            r"generent|"
            r"implique|"
            r"impliquent|"
            r"nécessite|"
            r"necessite|"
            r"nécessitent|"
            r"necessitent"
            r")\s+"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.92,
    ),
    RelationPattern(
        pattern_id="copular_definition",
        expression=re.compile(
            rf"^\s*{SUBJECT}\s+"
            r"(?P<predicate>"
            r"est|"
            r"sont|"
            r"devient|"
            r"deviennent"
            r")\s+"
            rf"{OBJECT}"
            r"\s*[.!?]?\s*$",
            flags=re.IGNORECASE,
        ),
        confidence=0.88,
    ),
)