from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from agentic_qa.rag.base import DocumentChunk, RetrievedChunk, VectorStore


@dataclass(slots=True)
class _StoredEntry:
    chunk: DocumentChunk
    embedding: list[float]


class InMemoryVectorStore(VectorStore):
    def __init__(self, persistence_path: Path | None = None) -> None:
        self.persistence_path = persistence_path
        self._entries: list[_StoredEntry] = []
        if self.persistence_path is not None and self.persistence_path.exists():
            self._load()

    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._entries.append(_StoredEntry(chunk=chunk, embedding=embedding))
        self._persist()

    def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        if top_k <= 0:
            return []
        scored = [
            RetrievedChunk(chunk=entry.chunk, score=self._cosine_similarity(query_embedding, entry.embedding))
            for entry in self._entries
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def clear(self) -> None:
        self._entries = []
        self._persist()

    def size(self) -> int:
        return len(self._entries)

    def _persist(self) -> None:
        if self.persistence_path is None:
            return
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "chunk": asdict(entry.chunk),
                "embedding": entry.embedding,
            }
            for entry in self._entries
        ]
        self.persistence_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self) -> None:
        raw = json.loads(self.persistence_path.read_text(encoding="utf-8"))
        self._entries = [
            _StoredEntry(
                chunk=DocumentChunk(**item["chunk"]),
                embedding=[float(value) for value in item["embedding"]],
            )
            for item in raw
        ]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        numerator = sum(l_value * r_value for l_value, r_value in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)