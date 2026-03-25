# Release 1 Architecture

Release 1 is a single vertical slice.

- Input: API feature validation request
- Planning: deterministic run plan generation
- Generation: Python and Robot test skeletons
- Execution: run both against the bundled sample SUT
- Evidence: artifacts and logs under `artifacts/runs/<run_id>/`
- Output: structured run summary

The implementation is intentionally narrow and does not include generalized orchestration, browser automation, or live retrieval infrastructure.
