from __future__ import annotations

from dataclasses import dataclass

from agentic_qa.rag.retriever import Retriever


@dataclass(slots=True)
class RetrievalFixture:
    query: str
    expected_document_id: str


def evaluate_recall_at_k(retriever: Retriever, fixtures: list[RetrievalFixture], *, top_k: int = 3) -> dict[str, float | int]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    hits = 0
    for fixture in fixtures:
        results = retriever.retrieve(fixture.query, top_k=top_k)
        document_ids = {result.chunk.document_id for result in results}
        if fixture.expected_document_id in document_ids:
            hits += 1

    total = len(fixtures)
    recall = hits / total if total else 0.0
    return {
        "queries": total,
        "hits": hits,
        "top_k": top_k,
        "recall_at_k": recall,
    }