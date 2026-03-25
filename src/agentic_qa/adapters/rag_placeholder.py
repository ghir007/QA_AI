class RAGPlaceholderAdapter:
    """Placeholder seam for future retrieval-backed QA support."""

    def describe(self) -> dict[str, str]:
        return {
            "status": "stub",
            "purpose": "Future RAG ingestion and retrieval integration seam.",
        }