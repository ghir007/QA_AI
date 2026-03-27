from agentic_qa.rag.base import SourceDocument
from agentic_qa.rag.chunking import FixedSizeOverlapChunker, SentenceWindowChunker


def test_fixed_size_overlap_chunker_creates_overlapping_chunks() -> None:
    document = SourceDocument(
        document_id="doc-1",
        text="abcdefghijklmnopqrstuvwxyz",
        uri="memory://doc-1",
        media_type="text/plain",
    )

    chunks = FixedSizeOverlapChunker(chunk_size=10, overlap=4).chunk([document])

    assert len(chunks) == 4
    assert chunks[0].text == "abcdefghij"
    assert chunks[1].text.startswith("ghij")


def test_sentence_window_chunker_groups_sentences() -> None:
    document = SourceDocument(
        document_id="doc-2",
        text="One sentence. Two sentence. Three sentence. Four sentence.",
        uri="memory://doc-2",
        media_type="text/plain",
    )

    chunks = SentenceWindowChunker(window_size=2, overlap=1).chunk([document])

    assert len(chunks) == 3
    assert "One sentence." in chunks[0].text
    assert "Two sentence." in chunks[0].text