# Release 1 Architecture

Release 1 is a single vertical slice.

- Input: API feature validation request
- Planning: deterministic run plan generation
- Generation: Python and Robot test skeletons
- Execution: run both against the bundled sample SUT
- Evidence: artifacts and logs under `artifacts/runs/<run_id>/`
- Output: structured run summary

The implementation is intentionally narrow and does not include generalized orchestration, browser automation, or live retrieval infrastructure.

## Release 3 Failure Analysis

Release 3 adds an optional post-execution failure-analysis step that reads only persisted run evidence from `summary.json`, generated artifacts, and execution logs. When `ANALYZE_FAILURES=true`, the run service invokes a deterministic local rule-based analyzer after overall status is computed, writes a `failure_analysis.json` artifact beside the existing run evidence, and includes a `failure_analysis` object in the summary. When disabled, the workflow contract remains unchanged and the additional field is omitted.

## Release 4 Release Orchestration

Release 4 adds a deterministic risk scorer and release-readiness planner for batches of persisted workflow requests. When `ENABLE_RELEASE_ORCHESTRATION=true`, the API exposes `GET /release-readiness` to load persisted request artifacts and prior summaries from run directories, score each request by deterministic risk factors, and return a prioritized readiness summary with a recommended suite and release recommendation. The layer is advisory only, does not execute tests, and remains optional and auditable.
