"""ScheduleItem domain model. Single dated items only -- no recurrence in Phase 1."""

from datetime import date, time
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ScheduleItemStatus = Literal["planned", "completed", "skipped"]


class ScheduleItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    date: date
    start_time: time
    duration_minutes: int
    status: ScheduleItemStatus = "planned"
    goal_id: str | None = None
    notes: str | None = None
