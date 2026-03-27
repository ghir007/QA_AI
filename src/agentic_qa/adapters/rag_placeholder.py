from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_qa.domain.models import FeatureValidationRequest
from agentic_qa.rag.chunking import FixedSizeOverlapChunker
from agentic_qa.rag.embedding import DeterministicStubEmbedder
from agentic_qa.rag.retriever import Retriever, format_retrieved_context
from agentic_qa.rag.sources import LocalFileDocumentSource
from agentic_qa.rag.vector_store import InMemoryVectorStore


@dataclass(slots=True)
class LocalRAGAdapter:
    retriever: Retriever
    top_k: int = 3
    source_root: Path | None = None

    def describe(self) -> dict[str, str | int]:
        return {
            "status": "ready",
            "mode": "local",
            "top_k": self.top_k,
            "source_root": str(self.source_root) if self.source_root is not None else "",
        }

    def retrieve_context(self, request: FeatureValidationRequest) -> str:
        query = self._build_query(request)
        results = self.retriever.retrieve(query, top_k=self.top_k)
        return format_retrieved_context(results)

    @staticmethod
    def _build_query(request: FeatureValidationRequest) -> str:
        negative_cases = ", ".join(request.negative_cases) if request.negative_cases else "none"
        return " | ".join(
            [
                request.feature_name,
                request.feature_description,
                request.target_endpoint.method.upper(),
                request.target_endpoint.path,
                f"expected_status={request.expected_status_code}",
                f"expected_fields={','.join(request.expected_response_fields)}",
                f"negative_cases={negative_cases}",
            ]
        )


RAGPlaceholderAdapter = LocalRAGAdapter


def create_local_rag_adapter(
    source_root: Path,
    *,
    chunk_size: int = 320,
    chunk_overlap: int = 64,
    top_k: int = 3,
    persistence_path: Path | None = None,
) -> LocalRAGAdapter:
    retriever = Retriever(
        source=LocalFileDocumentSource(source_root),
        chunker=FixedSizeOverlapChunker(chunk_size=chunk_size, overlap=chunk_overlap),
        embedder=DeterministicStubEmbedder(),
        vector_store=InMemoryVectorStore(persistence_path=persistence_path),
    )
    retriever.ingest(rebuild=True)
    return LocalRAGAdapter(retriever=retriever, top_k=top_k, source_root=source_root)