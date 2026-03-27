from __future__ import annotations

from dataclasses import dataclass

from agentic_qa.rag.base import Chunker, DocumentSource, Embedder, RetrievedChunk, VectorStore
from agentic_qa.rag.reranking import Reranker


@dataclass(slots=True)
class IngestionReport:
    document_count: int
    chunk_count: int


class Retriever:
    def __init__(
        self,
        source: DocumentSource,
        chunker: Chunker,
        embedder: Embedder,
        vector_store: VectorStore,
        reranker: Reranker | None = None,
    ) -> None:
        self.source = source
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.reranker = reranker

    def ingest(self, *, rebuild: bool = True) -> IngestionReport:
        documents = self.source.load()
        chunks = self.chunker.chunk(documents)
        if rebuild:
            self.vector_store.clear()
        if chunks:
            self.vector_store.add(chunks, self.embedder.embed_texts([chunk.text for chunk in chunks]))
        return IngestionReport(document_count=len(documents), chunk_count=len(chunks))

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        query_embedding = self.embedder.embed_texts([query])[0]
        results = self.vector_store.search(query_embedding, top_k=top_k)
        if self.reranker is not None:
            return self.reranker.rerank(query, results)
        return results


def format_retrieved_context(results: list[RetrievedChunk]) -> str:
    if not results:
        return ""

    lines = ["Retrieved QA context:"]
    for index, result in enumerate(results, start=1):
        snippet = " ".join(result.chunk.text.split())
        if len(snippet) > 180:
            snippet = f"{snippet[:177]}..."
        lines.append(
            f"{index}. source={result.chunk.document_id} score={result.score:.4f} text={snippet}"
        )
    return "\n".join(lines)