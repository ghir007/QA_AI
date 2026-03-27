from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_qa.rag.base import RetrievedChunk


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, results: list[RetrievedChunk]) -> list[RetrievedChunk]:
        raise NotImplementedError