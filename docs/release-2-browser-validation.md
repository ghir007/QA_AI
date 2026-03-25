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
- An MCP-backed adapter boundary exists, but live connectivity remains optional.
- When no browser executor is configured, browser behavior remains deterministic and non-breaking.
- Existing Release 1 callers remain compatible when the browser flag is omitted.

This keeps Release 2 narrow and demonstrable without introducing a generalized workflow engine, background workers, or live retrieval features.
