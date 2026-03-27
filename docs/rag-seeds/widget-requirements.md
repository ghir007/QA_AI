# Widget Creation Requirements

Feature: create widget

- The system exposes `POST /api/v1/widgets` for widget creation.
- A valid request requires header `X-API-Key: demo-key`.
- A valid request body includes `name` with at least 3 characters.
- `priority` supports `low`, `normal`, and `high`.
- A successful response returns HTTP `201`.
- A successful response body includes `id`, `name`, `priority`, and `status`.
- The sample UI flow posts the widget form from `/widgets/ui` to the same API endpoint.