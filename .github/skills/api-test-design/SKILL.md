---
name: api-test-design
description: Design deterministic API validation coverage for the current workflow.
---

Use this skill when the task is to shape or review API-level coverage for `api_feature_validation_v1`.

Use it for:
- turning a structured feature request into happy-path and negative-path checks
- deciding what Python and Robot generation should cover
- checking whether browser validation should stay off or be requested for the current sample UI path
- validating that proposed coverage stays within current request and summary contracts

Expected output:
1. Request assumptions
2. Happy-path API checks
3. Negative-path API checks
4. Expected generated Python test behavior
5. Expected generated Robot suite behavior
6. Optional browser-validation decision and expected fallback semantics
7. Artifact and summary expectations

Constraints:
- Keep scope within the existing workflow and bundled sample SUT.
- Do not invent new workflows or future orchestration layers.
- Do not treat browser validation as mandatory.
- Keep MCP guidance honest: browser validation can use the narrow adapter path, but deterministic fallback remains valid behavior.