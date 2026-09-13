"""UserProfile domain model."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

EnergyLevel = Literal["low", "medium", "high"]


class MoodEntry(BaseModel):
    """One log_mood() entry -- an append-only history, not just a snapshot."""

    mood: str
    energy: EnergyLevel | None = None
    note: str | None = None
    logged_at: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    name: str
    interests: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    mood_log: list[MoodEntry] = Field(default_factory=list)
    created_date: date = Field(default_factory=date.today)

    @property
    def latest_mood(self) -> MoodEntry | None:
        return self.mood_log[-1] if self.mood_log else None
