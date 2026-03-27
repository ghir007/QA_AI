# RAG Placeholders

Release 2 now includes a real local retrieval subsystem behind the original seam.

Real now:

- `src/agentic_qa/adapters/rag_placeholder.py` promotes the seam into a local/dev-safe adapter factory.
- Local document loading supports markdown, JSON, and plain-text files.
- Chunking is implemented with replaceable abstractions, including a fixed-size overlap default and a sentence-window option.
- Embedding is implemented through a real adapter interface with a deterministic stub embedder that is safe for development and CI.
- Vector search is implemented with an in-memory cosine-similarity store and optional JSON file persistence.
- Retrieval is implemented and can inject retrieved context into generator inputs when explicitly enabled.
- A recall@k evaluation helper is available for fixture-based test validation.

Still placeholder or intentionally stubbed:

- No live external embedding service is connected.
- No live external vector database is connected.
- No reranker implementation is provided yet; only the interface exists.
- No retrieval is enabled by default in the main workflow.

Current activation model:

- `ENABLE_RAG_CONTEXT=false` keeps the existing `api_feature_validation_v1` behavior unchanged.
- `ENABLE_RAG_CONTEXT=true` enables local seed-doc ingestion and retrieval-backed context enrichment before test generation.
