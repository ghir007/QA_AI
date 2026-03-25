---
agent: qa-reviewer
description: Triage a Release 1 API validation run
---

Review a Release 1 run using the run summary and available artifacts only.

Required output:
1. Failure classification: application, generated test, configuration, environment, or artifact handling
2. Evidence used: summary fields, logs, generated files, and Robot outputs when present
3. Most likely root cause
4. Smallest corrective action within current Release 1 scope
5. Whether the issue affects Python execution, Robot execution, or both

Constraints:
- Do not propose new features or broader architecture changes.
- Focus on the existing `api_feature_validation_v1` workflow.
- Prefer findings tied to concrete artifacts and current contract behavior.