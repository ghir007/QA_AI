from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceDocument:
    document_id: str
    text: str
    uri: str
    media_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


class DocumentSource(ABC):
    @abstractmethod
    def load(self) -> list[SourceDocument]:
        raise NotImplementedError


class Chunker(ABC):
    @abstractmethod
    def chunk(self, documents: list[SourceDocument]) -> list[DocumentChunk]:
        raise NotImplementedError


class Embedder(ABC):
    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class VectorStore(ABC):
    @abstractmethod
    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError