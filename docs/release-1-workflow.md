# Release 1 Workflow Contract

Workflow name: `api_feature_validation_v1`

Steps:

1. Validate request
2. Generate run plan
3. Generate Python test skeleton
4. Generate Robot test skeleton
5. Execute Python test path
6. Execute Robot test path
7. Collect artifacts
8. Return summary

Failure rules:

- Invalid request stops immediately
- Generation failures stop execution
- Python and Robot execution failures are isolated and summarized independently
