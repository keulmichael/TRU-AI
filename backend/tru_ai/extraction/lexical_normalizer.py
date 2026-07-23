from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedText:
    text: str
    original_indexes: tuple[int, ...]


class LexicalNormalizer:
    """Normalise le texte tout en conservant les positions d'origine."""

    APOSTROPHES = {
        "’",
        "‘",
        "ʼ",
        "`",
        "´",
    }

    DASHES = {
        "‐",
        "-",
        "‒",
        "–",
        "—",
        "―",
    }

    def normalize(self, value: str) -> str:
        return self.normalize_with_mapping(value).text

    def normalize_with_mapping(
        self,
        value: str,
    ) -> NormalizedText:
        normalized_characters: list[str] = []
        original_indexes: list[int] = []

        previous_was_space = False

        for original_index, character in enumerate(value):
            character = self.standardize_character(character)

            decomposed = unicodedata.normalize(
                "NFKD",
                character,
            )

            for decomposed_character in decomposed:
                if unicodedata.combining(
                    decomposed_character
                ):
                    continue

                lowered_character = (
                    decomposed_character.lower()
                )

                if lowered_character.isspace():
                    if (
                        normalized_characters
                        and not previous_was_space
                    ):
                        normalized_characters.append(" ")
                        original_indexes.append(
                            original_index
                        )

                    previous_was_space = True
                    continue

                if lowered_character.isalnum():
                    normalized_characters.append(
                        lowered_character
                    )
                    original_indexes.append(
                        original_index
                    )
                    previous_was_space = False
                    continue

                if lowered_character == "'":
                    normalized_characters.append("'")
                    original_indexes.append(
                        original_index
                    )
                    previous_was_space = False
                    continue

                if (
                    normalized_characters
                    and not previous_was_space
                ):
                    normalized_characters.append(" ")
                    original_indexes.append(
                        original_index
                    )

                previous_was_space = True

        while (
            normalized_characters
            and normalized_characters[-1] == " "
        ):
            normalized_characters.pop()
            original_indexes.pop()

        return NormalizedText(
            text="".join(normalized_characters),
            original_indexes=tuple(original_indexes),
        )

    def slugify(self, value: str) -> str:
        normalized = self.normalize(value)
        normalized = normalized.replace("'", "-")
        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            normalized,
        )

        return normalized.strip("-")

    def standardize_character(
        self,
        character: str,
    ) -> str:
        if character in self.APOSTROPHES:
            return "'"

        if character in self.DASHES:
            return "-"

        return character