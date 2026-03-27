---
name: browser-validation-path
description: Reason about the current optional browser-validation path and its deterministic fallback behavior.
---

Use this skill when the task involves the current browser-validation path in Release 2.

Use it for:
- deciding whether `enable_browser_validation` should be used for a task
- checking expected generated browser validation artifacts for the sample UI path
- reasoning about `passed`, `failed`, and `skipped` browser outcomes
- reviewing the boundary between planner, run service, browser executor, and MCP browser adapter
- checking whether MCP-related behavior is real current behavior or still placeholder

Current behavior to preserve:
- browser validation is optional within `api_feature_validation_v1`
- browser execution runs through the `BrowserExecutor` boundary
- fake and unavailable paths are deterministic
- the MCP browser adapter path is real but narrow and stdio-based
- MCP startup, timeout, protocol, or artifact failures can deterministically produce browser `skipped`
- skipped browser execution is non-participating in overall status

Constraints:
- Do not invent a new browser workflow.
- Do not imply that browser validation is always required.
- Do not describe RAG as implemented.
- Keep recommendations tied to the current sample UI path and current contracts.