import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from job_system.models import JobStatus


class JobCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "queue": "default",
                    "task_name": "generate-report",
                    "payload": {
                        "report_id": "sales-2026-09",
                        "format": "pdf",
                    },
                    "priority": 10,
                }
            ]
        }
    )

    queue: str = Field(
        default="default",
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )
    task_name: str = Field(
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=-100, le=100)

    @field_validator("queue", "task_name")
    @classmethod
    def reject_surrounding_whitespace(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("must not contain surrounding whitespace")

        return value


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    queue: str
    task_name: str
    payload: dict[str, Any]
    status: JobStatus
    priority: int
    attempt_count: int
    worker_id: str | None
    result: dict[str, Any] | None
    last_error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
