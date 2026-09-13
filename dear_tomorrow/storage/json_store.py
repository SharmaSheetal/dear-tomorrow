"""JSON-file-backed repository for domain state (profile, goals, schedule).

Single AppState blob written atomically (temp file + os.replace) so a crash mid-write
can't leave data/state.json corrupted. Tools build their logic on top of load_state()
and save_state() rather than touching the file directly.
"""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from dear_tomorrow.models.goal import Goal
from dear_tomorrow.models.schedule import ScheduleItem
from dear_tomorrow.models.user import UserProfile

STATE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "state.json"


class AppState(BaseModel):
    user_profile: UserProfile | None = None
    goals: list[Goal] = Field(default_factory=list)
    schedule_items: list[ScheduleItem] = Field(default_factory=list)


def load_state(path: Path = STATE_PATH) -> AppState:
    if not path.exists() or path.stat().st_size == 0:
        return AppState()
    with open(path, "r") as f:
        raw = json.load(f)
    if not raw:
        return AppState()
    return AppState.model_validate(raw)


def save_state(state: AppState, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        f.write(state.model_dump_json(indent=2))
    os.replace(tmp_path, path)
