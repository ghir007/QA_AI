---
name: failure-triage
description: Triage current workflow failures using persisted evidence.
---

Use this skill when a run failed, partially succeeded, or behaved unexpectedly and you need to diagnose it from artifacts.

Use it for:
- reading `summary.json`, logs, generated files, Robot outputs, and browser artifacts
- distinguishing application defects from generation, execution, configuration, environment, or artifact-handling issues
- separating expected deterministic browser fallback from real regressions
- identifying the smallest corrective action that preserves current scope and contracts

Recommended evidence order:
1. Run summary and overall status
2. Python and Robot metrics and logs
3. Browser metrics and browser artifacts when present
4. Generated test files and browser validation artifact
5. Configuration and environment assumptions only after artifact review

Constraints:
- Focus on the existing `api_feature_validation_v1` workflow.
- Do not propose new workflows or speculative platform features.
- Keep browser and MCP analysis honest about what is optional, narrow, and fallback-driven.