from agentic_qa.rag.base import DocumentChunk, SourceDocument
from agentic_qa.rag.chunking import FixedSizeOverlapChunker
from agentic_qa.rag.embedding import DeterministicStubEmbedder
from agentic_qa.rag.evaluation import RetrievalFixture, evaluate_recall_at_k
from agentic_qa.rag.retriever import Retriever
from agentic_qa.rag.sources import LocalFileDocumentSource
from agentic_qa.rag.vector_store import InMemoryVectorStore


def test_local_file_document_source_reads_json_and_markdown(tmp_path) -> None:
    (tmp_path / "doc.md").write_text("# Widget doc", encoding="utf-8")
    (tmp_path / "spec.json").write_text('{"endpoint":"/api/v1/widgets"}', encoding="utf-8")

    documents = LocalFileDocumentSource(tmp_path).load()

    assert {document.document_id for document in documents} == {"doc.md", "spec.json"}
    assert any('"endpoint": "/api/v1/widgets"' in document.text for document in documents)


def test_retriever_returns_relevant_chunk() -> None:
    class StaticSource:
        def load(self) -> list[SourceDocument]:
            return [
                SourceDocument("requirements.md", "create widget requires demo-key and returns 201", "memory://requirements", "text/markdown"),
                SourceDocument("failures.txt", "robot suites fail when the resource path is wrong", "memory://failures", "text/plain"),
            ]

    retriever = Retriever(
        source=StaticSource(),
        chunker=FixedSizeOverlapChunker(chunk_size=80, overlap=10),
        embedder=DeterministicStubEmbedder(dimensions=18),
        vector_store=InMemoryVectorStore(),
    )
    retriever.ingest()

    results = retriever.retrieve("How does create widget authenticate?", top_k=1)

    assert results[0].chunk.document_id == "requirements.md"


def test_recall_at_k_reports_hits() -> None:
    class StaticSource:
        def load(self) -> list[SourceDocument]:
            return [
                SourceDocument("requirements.md", "create widget requires demo-key and returns 201", "memory://requirements", "text/markdown"),
                SourceDocument("failures.txt", "robot suites fail when the resource path is wrong", "memory://failures", "text/plain"),
            ]

    retriever = Retriever(
        source=StaticSource(),
        chunker=FixedSizeOverlapChunker(chunk_size=80, overlap=10),
        embedder=DeterministicStubEmbedder(dimensions=18),
        vector_store=InMemoryVectorStore(),
    )
    retriever.ingest()

    report = evaluate_recall_at_k(
        retriever,
        [RetrievalFixture(query="Which header authenticates create widget?", expected_document_id="requirements.md")],
        top_k=1,
    )

    assert report["hits"] == 1
    assert report["recall_at_k"] == 1.0