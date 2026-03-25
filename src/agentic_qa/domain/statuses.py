from enum import StrEnum


class RunStatus(StrEnum):
    PLANNED = "planned"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    GENERATION_FAILED = "generation_failed"
    INVALID_REQUEST = "invalid_request"


class StepStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"