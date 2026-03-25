# Release 2 Browser Validation

Release 2 extends the existing `api_feature_validation_v1` workflow with one optional browser-validation path.

Slice 1 kept Release 1 as the backbone and added browser-requested planning plus deterministic unavailable behavior.

Slice 2 adds the narrow execution boundary:

1. Request intake
2. Deterministic run plan generation
3. Python API test generation and execution
4. Robot API test generation and execution
5. Deterministic browser validation artifact generation for the sample UI flow
6. Optional browser execution through a narrow executor boundary

Current slice boundaries:

- Browser validation is requested with `enable_browser_validation=true`.
- The bundled sample SUT now exposes a minimal UI page at `/widgets/ui`.
- Browser execution now runs through a `BrowserExecutor` boundary.
- A fake/local executor supports tests and development.
- An MCP-backed adapter boundary exists as a narrow optional stdio-based demo path, but live connectivity remains optional.
- When no browser executor is configured, browser behavior remains deterministic and non-breaking.
- Skipped browser execution does not change a fully passing or fully failing API/Robot result; it is treated as non-participating for overall status.
- Existing Release 1 callers remain compatible when the browser flag is omitted.

Current MCP demo support:

- `BROWSER_EXECUTOR=mcp` enables the real MCP-backed browser executor path.
- `MCP_BROWSER_COMMAND` points to the stdio MCP server process to launch.
- `MCP_BROWSER_ARGS_JSON` provides the command arguments as a JSON array string.
- `MCP_BROWSER_TOOL_NAME` defaults to `browser_validate_ui` and keeps the integration narrow.
- The generated browser validation artifact is sent to the MCP tool as structured JSON plus the sample SUT base URL.
- The executor materializes returned artifacts into the run directory, including `browser/browser_execution.log`, `browser/browser_result.json`, and `browser/browser_screenshot.png` when the MCP server returns one.
- If MCP startup, timeout, protocol exchange, or artifact materialization fails, browser validation deterministically falls back to `skipped` without breaking the API and Robot paths.

Minimal demo configuration:

1. Set `BROWSER_EXECUTOR=mcp`.
2. Set `MCP_BROWSER_COMMAND` to the browser MCP server executable.
3. Set `MCP_BROWSER_ARGS_JSON` to a JSON array of arguments required by that server.
4. Keep `enable_browser_validation=true` in the run request.
5. Start the sample SUT and platform API, then submit the existing workflow request as normal.

This keeps Release 2 narrow and demonstrable without introducing a generalized workflow engine, background workers, or live retrieval features.
