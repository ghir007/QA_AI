---
agent: qa-reviewer
description: Triage a current API validation run using artifacts and summary output
---

Review a run of `api_feature_validation_v1` using the run summary and available artifacts only.

Required output:
1. Failure classification: application, generated test, configuration, environment, execution path, MCP browser adapter, or artifact handling
2. Evidence used: summary fields, logs, generated files, Robot outputs, and browser artifacts when present
3. Most likely root cause
4. Smallest corrective action within current scope
5. Which paths are affected: Python, Robot, browser, or multiple
6. Whether browser fallback was expected deterministic behavior or an unexpected regression

Constraints:
- Do not propose new features or broader architecture changes.
- Focus on the existing `api_feature_validation_v1` workflow.
- Treat browser validation as optional and non-participating when skipped.
- Prefer findings tied to concrete artifacts and current contract behavior.