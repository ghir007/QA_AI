# Agentic QA Copilot

Agentic QA Copilot is a QA-first Python platform scaffold focused on a single credible Release 1 workflow.

Release 1 accepts a structured API feature validation request, generates deterministic Python and Robot API test skeletons, executes them against a bundled sample system under test, collects artifacts, and returns a structured summary.

## Release 1 Scope

- One workflow: `api_feature_validation_v1`
- One bundled sample SUT for reproducible local and CI execution
- One Python API execution path
- One Robot API execution path
- Structured artifacts, logs, and run summaries
- MCP and RAG placeholders only

## Quick Start

1. Create a virtual environment and install dependencies.
2. Start the sample SUT.
3. Start the platform API.
4. Submit a workflow request to `/runs`.

For the full operator workflow, environment variables, request examples, and test commands, see `README_USAGE.md`.

## Optional MCP Browser Demo

Release 2 keeps browser validation optional and off by default. The MCP path is a narrow optional stdio-based demo integration for the sample UI flow:

1. Set `BROWSER_EXECUTOR=mcp`.
2. Set `MCP_BROWSER_COMMAND` to a stdio MCP server executable.
3. Set `MCP_BROWSER_ARGS_JSON` to a JSON array string for that server's arguments.
4. Optionally override `MCP_BROWSER_TOOL_NAME` if your MCP server exposes a different narrow browser-validation tool.
5. Submit the same `/runs` request with `enable_browser_validation=true`.

When configured, the platform still uses the same workflow contract and writes browser artifacts into the run directory beside the Python and Robot evidence. If MCP startup, timeout, protocol exchange, or artifact materialization fails, browser validation deterministically falls back to `skipped` and the API/Robot workflow remains unchanged.

## Repository Layout

- `src/agentic_qa/` main platform source
- `sample_sut/` bundled API under test
- `robot/` Robot resources, generated suites, and execution outputs
- `tests/` unit, integration, and end-to-end tests
- `docs/` architecture and workflow notes
- `.github/` Copilot customization files
- `.vscode/` MCP placeholder config

## Release Roadmap

- Release 1: API feature validation vertical slice
- Release 2: MCP-backed browser validation and RAG-backed retrieval seams become real integrations
- Release 3: failure analysis and self-healing guidance
- Release 4: risk-based orchestration and release-readiness reporting
