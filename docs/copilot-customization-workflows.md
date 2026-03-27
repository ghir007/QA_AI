# Copilot Customization Workflows

This repository keeps the customization layer small on purpose.

The intended usage is:

- `copilot-instructions.md` anchors Copilot to the real repository behavior and current scope discipline.
- `qa-planner` is for planning work inside the current workflow and contracts only.
- `qa-implementer` is for approved code changes that preserve the current request, artifact, and summary behavior unless explicitly changed.
- `qa-reviewer` is for findings-first review of regressions, weak evidence, and missing tests.
- `plan-api-feature-validation.prompt.md` is for planning or re-planning a concrete feature-validation request.
- `triage-api-run.prompt.md` is for artifact-first run triage.
- `api-test-design` helps shape deterministic request coverage.
- `failure-triage` helps diagnose failures from persisted evidence.
- `browser-validation-path` helps with the current optional browser path and its fallback semantics.

What this customization layer does not do:

- it does not introduce new workflows
- it does not imply RAG is implemented
- it does not describe a generalized agent framework
- it does not broaden the current Release 2 browser path beyond what exists in the codebase

Use the smallest tool or file that fits the task. The goal is to keep Copilot accurate, operational, and aligned with the repository as it exists now.
