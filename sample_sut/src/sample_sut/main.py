from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(title="Sample SUT", version="0.1.0")


class WidgetCreateRequest(BaseModel):
    name: str = Field(min_length=3)
    priority: str = Field(default="normal")


class WidgetResponse(BaseModel):
    id: str
    name: str
    priority: str
    status: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/widgets/ui", response_class=HTMLResponse)
def widgets_ui() -> HTMLResponse:
        return HTMLResponse(
                """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>Widget Manager</title>
    </head>
    <body>
        <main>
            <h1>Create Widget</h1>
            <form id="create-widget-form">
                <label for="widget-name">Name</label>
                <input id="widget-name" name="name" type="text" required minlength="3" />

                <label for="widget-priority">Priority</label>
                <select id="widget-priority" name="priority">
                    <option value="low">low</option>
                    <option value="normal" selected>normal</option>
                    <option value="high">high</option>
                </select>

                <button id="submit-widget" type="submit">Create</button>
            </form>

            <div id="result" role="status"></div>
        </main>

        <script>
            const form = document.getElementById("create-widget-form");
            const result = document.getElementById("result");

            form.addEventListener("submit", async (event) => {
                event.preventDefault();

                const payload = {
                    name: document.getElementById("widget-name").value,
                    priority: document.getElementById("widget-priority").value,
                };

                const response = await fetch("/api/v1/widgets", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-API-Key": "demo-key",
                    },
                    body: JSON.stringify(payload),
                });

                const body = await response.json();
                if (response.ok) {
                    result.textContent = `Widget created: ${body.id}`;
                } else {
                    result.textContent = `Error: ${body.detail}`;
                }
            });
        </script>
    </body>
</html>
""".strip()
        )


@app.post("/api/v1/widgets", response_model=WidgetResponse, status_code=201)
def create_widget(
    payload: WidgetCreateRequest,
    x_api_key: str | None = Header(default=None),
) -> WidgetResponse:
    if x_api_key != "demo-key":
        raise HTTPException(status_code=401, detail="invalid api key")

    if payload.priority not in {"low", "normal", "high"}:
        raise HTTPException(status_code=422, detail="invalid priority")

    return WidgetResponse(
        id="widget-001",
        name=payload.name,
        priority=payload.priority,
        status="created",
    )