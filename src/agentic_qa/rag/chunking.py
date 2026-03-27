from __future__ import annotations

import re

from agentic_qa.rag.base import Chunker, DocumentChunk, SourceDocument


class FixedSizeOverlapChunker(Chunker):
    def __init__(self, chunk_size: int = 320, overlap: int = 64) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        self.chunk_size = chunk_size
        self.overlap = min(overlap, max(chunk_size - 1, 0))

    def chunk(self, documents: list[SourceDocument]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        step = max(self.chunk_size - self.overlap, 1)
        for document in documents:
            text = document.text.strip()
            if not text:
                continue
            for start in range(0, len(text), step):
                window = text[start:start + self.chunk_size]
                if not window:
                    continue
                index = len(chunks)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}#chunk-{index}",
                        document_id=document.document_id,
                        text=window,
                        metadata={
                            "start": start,
                            "end": start + len(window),
                            **document.metadata,
                        },
                    )
                )
                if start + self.chunk_size >= len(text):
                    break
        return chunks


class SentenceWindowChunker(Chunker):
    SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, window_size: int = 3, overlap: int = 1) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        self.window_size = window_size
        self.overlap = min(overlap, max(window_size - 1, 0))

    def chunk(self, documents: list[SourceDocument]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        step = max(self.window_size - self.overlap, 1)
        for document in documents:
            sentences = [sentence.strip() for sentence in self.SENTENCE_PATTERN.split(document.text.strip()) if sentence.strip()]
            if not sentences:
                continue
            for start in range(0, len(sentences), step):
                window = sentences[start:start + self.window_size]
                if not window:
                    continue
                index = len(chunks)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}#sentence-{index}",
                        document_id=document.document_id,
                        text=" ".join(window),
                        metadata={"sentence_start": start, "sentence_end": start + len(window), **document.metadata},
                    )
                )
                if start + self.window_size >= len(sentences):
                    break
        return chunks