---
agent: qa-planner
description: Plan the Release 1 API feature validation workflow
---

Plan only for the existing `api_feature_validation_v1` workflow.

Required output:
1. Request assumptions
2. Happy-path API checks
3. Negative-path API checks
4. Expected generated Python test file
5. Expected generated Robot suite
6. Expected artifacts and summary fields
7. Risks or gaps within current Release 1 scope

Constraints:
- Do not propose new workflows.
- Do not expand into browser automation, RAG, MCP connectivity, or CI redesign.
- Keep recommendations tied to the bundled sample SUT and the current request, artifact, and summary contracts.
- Prefer deterministic, QA-first checks over generic architecture discussion.