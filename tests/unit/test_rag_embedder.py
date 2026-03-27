from agentic_qa.rag.embedding import DeterministicStubEmbedder


def test_stub_embedder_is_deterministic() -> None:
    embedder = DeterministicStubEmbedder(dimensions=12)

    first = embedder.embed_texts(["create widget"])[0]
    second = embedder.embed_texts(["create widget"])[0]

    assert first == second
    assert len(first) == 12


def test_stub_embedder_differs_for_different_queries() -> None:
    embedder = DeterministicStubEmbedder(dimensions=12)

    left = embedder.embed_texts(["create widget"])[0]
    right = embedder.embed_texts(["invalid api key"])[0]

    assert left != right