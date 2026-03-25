from fastapi import FastAPI

from agentic_qa.api.routes import router
from agentic_qa.observability.logging import configure_logging


def create_app() -> FastAPI:
	configure_logging()
	app = FastAPI(title="Agentic QA Copilot", version="0.1.0")
	app.include_router(router)
	return app


app = create_app()