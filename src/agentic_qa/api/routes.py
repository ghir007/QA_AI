from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from agentic_qa.api.schemas import RunRequest, RunResponse
from agentic_qa.orchestration.run_service import create_run_service


router = APIRouter()


def get_run_service():
    return create_run_service()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs", response_model=RunResponse)
def create_run(request: RunRequest, run_service: Annotated[object, Depends(get_run_service)]) -> RunResponse:
    return run_service.execute(request)


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str, run_service: Annotated[object, Depends(get_run_service)]) -> RunResponse:
    result = run_service.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="run not found")
    return result