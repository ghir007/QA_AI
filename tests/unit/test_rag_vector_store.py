import json

from agentic_qa.rag.base import DocumentChunk
from agentic_qa.rag.vector_store import InMemoryVectorStore


def test_vector_store_returns_ranked_results(tmp_path) -> None:
    store = InMemoryVectorStore()
    chunks = [
        DocumentChunk(chunk_id="a", document_id="req", text="create widget requirements"),
        DocumentChunk(chunk_id="b", document_id="fail", text="robot failure pattern"),
    ]
    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])

    results = store.search([0.9, 0.1], top_k=1)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "a"


def test_vector_store_can_persist_to_file(tmp_path) -> None:
    path = tmp_path / "store.json"
    store = InMemoryVectorStore(persistence_path=path)
    store.add(
        [DocumentChunk(chunk_id="a", document_id="req", text="create widget")],
        [[1.0, 0.0, 0.0]],
    )

    reloaded = InMemoryVectorStore(persistence_path=path)

    assert reloaded.size() == 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload[0]["chunk"]["chunk_id"] == "a"