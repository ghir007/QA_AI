# RAG Architecture

The Release 2 RAG subsystem is deliberately local, deterministic, and replaceable.

## Lifecycle

1. A document source loads local markdown, JSON, and plain-text files from `docs/rag-seeds` by default.
2. A chunker splits those documents into retrieval chunks. The default implementation uses fixed-size chunks with overlap; a sentence-window implementation is also available.
3. The embedder converts chunk text into vectors. The default embedder is a deterministic stub so development and CI stay offline and reproducible.
4. The vector store keeps chunk vectors in memory and can optionally persist them as JSON.
5. The retriever embeds the query, performs cosine-similarity search, and returns ranked chunks.
6. A reranker interface exists for future upgrades but is intentionally not implemented yet.
7. The run orchestration can call the retriever before generation when `ENABLE_RAG_CONTEXT=true` and pass the formatted context into generator inputs.

## Current Defaults

- Source root: `docs/rag-seeds`
- Embedder: deterministic stub
- Vector store: in-memory
- Persistence: off unless `RAG_VECTOR_STORE_PATH` is set
- Retrieval: off unless `ENABLE_RAG_CONTEXT=true`

## Seed Content

The repository ships with QA-specific seed documents for the bundled sample SUT:

- widget creation requirements
- widget API contract extract
- known failure patterns for API, Robot, and browser behavior

## Upgrade Boundaries

Every RAG component is behind an abstract interface so Release 3 can swap in a real embedder, persistent vector store, or reranker without changing the workflow contract.
