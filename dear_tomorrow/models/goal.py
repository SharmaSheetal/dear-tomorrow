"""Goal domain model."""

from datetime import date
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

GoalArea = Literal[
    "learning",
    "creativity",
    "fitness",
    "social",
    "exploration",
    "hobby",
    "personal_project",
    "career",
    "independence",
]

GoalStatus = Literal["active", "completed", "abandoned"]


class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    area: GoalArea
    status: GoalStatus = "active"
    created_date: date = Field(default_factory=date.today)
    notes: str | None = None
