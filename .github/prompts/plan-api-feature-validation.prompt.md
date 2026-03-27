---
agent: qa-planner
description: Plan the current API feature validation workflow
---

Plan only for the existing `api_feature_validation_v1` workflow as it exists in this repository today.

Required output:
1. Request assumptions
2. Happy-path API checks
3. Negative-path API checks
4. Whether browser validation should stay disabled or be requested
5. Expected generated Python test file
6. Expected generated Robot suite
7. Expected browser validation artifact and fallback behavior when browser validation is enabled
8. Expected artifacts and summary fields
9. Risks or gaps within current scope

Constraints:
- Do not propose new workflows.
- Do not expand into RAG, new MCP transports, or CI redesign.
- Keep recommendations tied to the bundled sample SUT and current request, artifact, and summary contracts.
- Treat browser validation as optional within the same workflow, not as a separate system.
- Keep MCP guidance honest: the browser adapter path is real but narrow and should retain deterministic fallback semantics.
- Prefer deterministic QA checks over generic architecture discussion.