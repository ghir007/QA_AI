# Copilot Instructions

This repository is QA-first and intentionally narrow.

- Optimize for the existing `api_feature_validation_v1` workflow unless the user explicitly expands scope.
- Preserve the current stable flow: request intake, deterministic run plan generation, Python API generation and execution, Robot generation and execution, optional browser validation, artifact capture, and structured run summary output.
- Keep the bundled sample SUT as the default validation target for local and CI work.
- Treat browser validation as optional and layered onto the existing workflow, not as a separate workflow.
- Treat the MCP browser path as real but narrow: it is a stdio-based demo integration behind the browser executor boundary with deterministic fallback behavior.
- Treat RAG as placeholder only in the current codebase.
- Prefer deterministic, testable implementations over speculative abstractions.
- Prefer small fixes to request handling, generation, execution, artifact handling, summary consistency, and test coverage over new architectural layers.
- Preserve current request, artifact, and run summary contracts unless the user explicitly asks to change them.
- When browser validation is requested, preserve current semantics for `passed`, `failed`, and `skipped`, including deterministic fallback when MCP is unavailable or malformed.
- Do not introduce new workflows, generic agent frameworks, background workers, or live external integrations without explicit approval.
- When behavior changes, update tests and docs so local and CI execution remain reproducible.
- Keep MCP and browser guidance honest about what is real, what is optional, and what still falls back deterministically.