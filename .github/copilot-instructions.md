# Copilot Instructions

This repository is QA-first and Release 1 is intentionally narrow.

- Prefer deterministic, testable implementations over speculative abstractions.
- Optimize for the existing `api_feature_validation_v1` workflow unless the user explicitly expands scope.
- Preserve the current Release 1 flow: request intake, deterministic run plan generation, Python API skeleton generation, Robot API skeleton generation, execution against the bundled sample SUT, artifact capture, and structured run summary output.
- Keep the bundled sample SUT as the default validation target for Release 1 work.
- Treat MCP and RAG as placeholders only in Release 1.
- Prioritize artifact capture, evidence, and reproducible execution.
- Prefer fixes to configuration, generation, execution, artifact handling, and summary consistency over new abstractions.
- Do not introduce generic agent frameworks, background workers, new workflow types, or external runtime dependencies without explicit approval.
- When behavior changes, update tests and docs so local and CI execution remain reproducible.
- Do not introduce secrets, live external integrations, or browser runtime dependencies without explicit approval.