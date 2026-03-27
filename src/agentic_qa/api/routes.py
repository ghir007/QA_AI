from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from agentic_qa.api.schemas import ReleaseReadinessResponse, RunRequest, RunResponse
from agentic_qa.config.settings import get_settings
from agentic_qa.orchestration.release_orchestrator import ReleaseOrchestrator, load_requests_and_summaries_from_run_ids
from agentic_qa.orchestration.run_service import create_run_service
from agentic_qa.storage.artifact_store import ArtifactStore


router = APIRouter()


def get_run_service():
    return create_run_service()


def get_release_orchestrator() -> ReleaseOrchestrator:
    return ReleaseOrchestrator()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs", response_model=RunResponse, response_model_exclude_none=True)
def create_run(request: RunRequest, run_service: Annotated[object, Depends(get_run_service)]) -> RunResponse:
    return run_service.execute(request)


@router.get("/runs/{run_id}", response_model=RunResponse, response_model_exclude_none=True)
def get_run(run_id: str, run_service: Annotated[object, Depends(get_run_service)]) -> RunResponse:
    result = run_service.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="run not found")
    return result


@router.get("/release-readiness", response_model=ReleaseReadinessResponse, response_model_exclude_none=True)
def get_release_readiness(
    run_ids: str,
    orchestrator: Annotated[ReleaseOrchestrator, Depends(get_release_orchestrator)],
) -> ReleaseReadinessResponse:
    settings = get_settings()
    if not settings.enable_release_orchestration:
        raise HTTPException(status_code=404, detail="release orchestration is disabled")

    parsed_run_ids = [value.strip() for value in run_ids.split(",") if value.strip()]
    artifact_store = ArtifactStore(settings.artifact_root)
    requests, prior_summaries = load_requests_and_summaries_from_run_ids(artifact_store, parsed_run_ids)
    return orchestrator.score_and_plan(requests, prior_summaries)