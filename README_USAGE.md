# Agentic QA Copilot Usage Guide

This repository is built around one primary workflow: `api_feature_validation_v1`.

The normal developer loop is:

1. Install the project in a Python 3.12 environment.
2. Start the bundled sample SUT.
3. Start the Agentic QA API.
4. Submit a validation request to `/runs`.
5. Inspect the returned summary and the persisted artifacts under `artifacts/runs/<run_id>/`.

## What This Repo Does

The platform accepts a structured request describing one API feature to validate. It then:

1. Generates a deterministic run plan.
2. Generates a Python API test file.
3. Generates a Robot Framework suite.
4. Executes the selected paths.
5. Optionally generates and executes browser validation.
6. Persists logs, generated files, and a structured run summary.

The bundled sample SUT is the default target for local work and CI.

## Prerequisites

- Python 3.12
- A shell that can run `python`
- Optional: Robot Framework browser demo dependencies only if you want the MCP browser path

## Installation

PowerShell example:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Start The Sample SUT

Run the bundled API under test on port `8010`:

```powershell
python -m uvicorn sample_sut.main:app --host 127.0.0.1 --port 8010
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8010/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Start The Agentic QA API

In a second terminal:

```powershell
python -m uvicorn agentic_qa.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Submit A Run

Example request body:

```json
{
  "request_id": "req-001",
  "feature_name": "create widget",
  "feature_description": "validate widget creation",
  "target_endpoint": {
    "path": "/api/v1/widgets",
    "method": "POST"
  },
  "expected_status_code": 201,
  "request_payload_example": {
    "name": "smoke-widget",
    "priority": "high"
  },
  "expected_response_fields": ["id", "name", "priority", "status"],
  "negative_cases": ["invalid_auth"],
  "execution_mode": "both",
  "tags": ["smoke"]
}
```

PowerShell example:

```powershell
$body = @'
{
  "request_id": "req-001",
  "feature_name": "create widget",
  "feature_description": "validate widget creation",
  "target_endpoint": {
    "path": "/api/v1/widgets",
    "method": "POST"
  },
  "expected_status_code": 201,
  "request_payload_example": {
    "name": "smoke-widget",
    "priority": "high"
  },
  "expected_response_fields": ["id", "name", "priority", "status"],
  "negative_cases": ["invalid_auth"],
  "execution_mode": "both",
  "tags": ["smoke"]
}
'@

Invoke-RestMethod \
  -Method Post \
  -Uri http://127.0.0.1:8000/runs \
  -ContentType 'application/json' \
  -Body $body
```

## Read A Run Summary

The API returns a `RunSummary` payload with:

- `run_id`
- `overall_status`
- `execution_summary`
- `artifacts`
- `errors`

Fetch a persisted run later with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/runs/<run_id>
```

## Artifact Layout

Each run is stored under `artifacts/runs/<run_id>/`.

Typical contents:

- `request.json`
- `run_plan.json`
- `summary.json`
- `generated/`
- `logs/`
- `robot/`
- `resources/common.resource`
- `browser/` when browser validation is requested

Important artifact keys returned in the summary often include:

- `plan_json`
- `generated_python_test`
- `generated_robot_suite`
- `python_log`
- `robot_log`
- `robot_output_xml`
- `robot_log_html`
- `robot_report_html`
- `generated_browser_validation`
- `browser_log`
- `browser_result_json`

## Execution Modes

The workflow currently supports these request values:

- `both`
- `python_only`
- `robot_only`

`both` is the normal path and is the best-covered mode in the current test suite.

## Optional Browser Validation

Browser validation is layered onto the same workflow. It is requested with `enable_browser_validation: true`.

### Fake Browser Executor

This is the easiest way to exercise the browser path locally.

```powershell
$env:BROWSER_EXECUTOR = 'fake'
$env:BROWSER_FAKE_OUTCOME = 'passed'
python -m uvicorn agentic_qa.main:app --host 127.0.0.1 --port 8000 --reload
```

### MCP Browser Executor

Use this only if you want to exercise the narrow stdio MCP demo path.

```powershell
$env:BROWSER_EXECUTOR = 'mcp'
$env:MCP_BROWSER_COMMAND = 'python'
$env:MCP_BROWSER_ARGS_JSON = '["tests/unit/mcp_demo_server.py"]'
$env:MCP_BROWSER_TOOL_NAME = 'browser_validate_ui'
python -m uvicorn agentic_qa.main:app --host 127.0.0.1 --port 8000 --reload
```

If MCP startup, protocol exchange, timeout handling, or artifact materialization fails, browser validation deterministically falls back to `skipped` and the API and Robot paths still complete.

## Optional RAG Context

RAG is local and opt-in.

```powershell
$env:ENABLE_RAG_CONTEXT = 'true'
python -m uvicorn agentic_qa.main:app --host 127.0.0.1 --port 8000 --reload
```

Seed documents live under `docs/rag-seeds/`. Retrieved context is added to generated artifacts as comments to make the behavior auditable.

## Optional Failure Analysis And Remediation

Failure analysis and remediation are deterministic post-processing layers.

```powershell
$env:ANALYZE_FAILURES = 'true'
$env:ENABLE_REMEDIATION = 'true'
python -m uvicorn agentic_qa.main:app --host 127.0.0.1 --port 8000 --reload
```

When enabled, additional artifacts may appear:

- `failure_analysis.json`
- `remediation_plan.json`

## Optional Release Readiness

Release readiness is an advisory API that scores persisted runs.

```powershell
$env:ENABLE_RELEASE_ORCHESTRATION = 'true'
python -m uvicorn agentic_qa.main:app --host 127.0.0.1 --port 8000 --reload
```

Example request:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/release-readiness?run_ids=<run_id_1>,<run_id_2>"
```

The response includes:

- `scored_requests`
- `recommended_suite`
- `release_recommendation`
- `advisory_note`

## Run Tests

Install dev dependencies, then run:

```powershell
pytest
```

Useful narrower commands:

```powershell
pytest tests/unit
pytest tests/integration
pytest tests/e2e
pytest sample_sut/tests
```

CI uses the same basic flow from `ci/jenkins/run_ci.sh`:

```powershell
python -m pip install -U pip
python -m pip install -e .[dev]
pytest
```

## Repo Pointers

- `src/agentic_qa/` platform implementation
- `sample_sut/` bundled API and UI under test
- `tests/` unit, integration, and end-to-end coverage
- `docs/` architecture and release notes
- `artifacts/runs/` persisted execution evidence

## Current Constraints

- The repo is intentionally optimized for the existing `api_feature_validation_v1` workflow.
- The bundled sample SUT is the default local and CI target.
- Browser validation is optional and should be treated as an extension of the existing workflow, not a separate system.
- The MCP browser path is a narrow demo integration with deterministic fallback behavior.
- RAG is still a controlled, local placeholder-style subsystem rather than a live external integration.
