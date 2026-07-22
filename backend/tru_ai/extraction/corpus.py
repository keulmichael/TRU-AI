from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusDocument:
    document_id: str
    title: str
    source_path: str
    content: str
    content_hash: str
    word_count: int


@dataclass(frozen=True)
class CorpusChunk:
    chunk_id: str
    document_id: str
    position: int
    content: str
    word_count: int


class CorpusManager:
    """Charge, normalise et segmente un corpus Markdown."""

    def __init__(
        self,
        corpus_directory: Path,
        chunk_size: int = 250,
        chunk_overlap: int = 40,
    ) -> None:
        self.corpus_directory = corpus_directory.resolve()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if chunk_size <= 0:
            raise ValueError("chunk_size doit être supérieur à zéro.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap ne peut pas être négatif.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap doit être strictement inférieur à chunk_size."
            )

    def discover(self) -> list[Path]:
        """Retourne tous les fichiers Markdown du corpus."""

        if not self.corpus_directory.exists():
            return []

        return sorted(
            path
            for path in self.corpus_directory.rglob("*.md")
            if path.is_file()
        )

    def load(self) -> list[CorpusDocument]:
        """Charge tous les documents Markdown."""

        return [self.load_document(path) for path in self.discover()]

    def load_document(self, path: Path) -> CorpusDocument:
        """Charge et normalise un document."""

        raw_content = path.read_text(encoding="utf-8-sig")
        content = self.normalize_text(raw_content)

        relative_path = path.resolve().relative_to(
            self.corpus_directory
        ).as_posix()

        title = self.extract_title(content, fallback=path.stem)
        document_id = self.build_document_id(relative_path)
        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        return CorpusDocument(
            document_id=document_id,
            title=title,
            source_path=relative_path,
            content=content,
            content_hash=content_hash,
            word_count=self.count_words(content),
        )

    def build_chunks(
        self,
        documents: list[CorpusDocument],
    ) -> list[CorpusChunk]:
        """Segmente les documents en blocs de mots avec chevauchement."""

        chunks: list[CorpusChunk] = []

        for document in documents:
            words = document.content.split()

            if not words:
                continue

            start = 0
            position = 0

            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                chunk_content = " ".join(words[start:end])

                chunk_id = f"{document.document_id}-chunk-{position:05d}"

                chunks.append(
                    CorpusChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        position=position,
                        content=chunk_content,
                        word_count=len(chunk_content.split()),
                    )
                )

                if end >= len(words):
                    break

                start = end - self.chunk_overlap
                position += 1

        return chunks

    @staticmethod
    def normalize_text(content: str) -> str:
        """Uniformise les sauts de ligne et les espaces superflus."""

        content = content.replace("\r\n", "\n").replace("\r", "\n")
        content = re.sub(r"[ \t]+\n", "\n", content)
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()

    @staticmethod
    def extract_title(content: str, fallback: str) -> str:
        """Extrait le premier titre Markdown de niveau 1."""

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("# "):
                title = stripped[2:].strip()

                if title:
                    return title

        return fallback.replace("-", " ").replace("_", " ").strip()

    @staticmethod
    def build_document_id(relative_path: str) -> str:
        """Produit un identifiant stable à partir du chemin relatif."""

        normalized_path = relative_path.lower().replace("\\", "/")
        digest = hashlib.sha256(
            normalized_path.encode("utf-8")
        ).hexdigest()[:12]

        slug = Path(relative_path).stem.lower()
        slug = re.sub(r"[^a-z0-9à-ÿ]+", "-", slug)
        slug = slug.strip("-")

        return f"{slug}-{digest}"

    @staticmethod
    def count_words(content: str) -> int:
        return len(content.split())

    @staticmethod
    def document_to_dict(document: CorpusDocument) -> dict:
        return asdict(document)

    @staticmethod
    def chunk_to_dict(chunk: CorpusChunk) -> dict:
        return asdict(chunk)