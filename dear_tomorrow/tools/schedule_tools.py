"""Tools for reading the schedule and creating schedule items.

Time-slot math (free time, overlap detection) is plain deterministic arithmetic here,
not something the LLM is asked to guess -- this is the guardrail against double-booked
or invalid times.
"""

from datetime import date, time, timedelta

from strands import tool

from dear_tomorrow.models.schedule import ScheduleItem
from dear_tomorrow.storage.json_store import load_state, save_state


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _to_time_str(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _overlaps(start1: int, end1: int, start2: int, end2: int) -> bool:
    return start1 < end2 and start2 < end1


@tool
def get_schedule(start_date: str, end_date: str | None = None) -> dict:
    """Return schedule items between start_date and end_date, inclusive.

    Args:
        start_date: ISO date (YYYY-MM-DD) to start from.
        end_date: ISO date (YYYY-MM-DD) to end at. If omitted, only start_date is returned.

    Returns:
        {"items": [...]} sorted by date then start time.
    """
    state = load_state()
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date) if end_date else start
    items = [i for i in state.schedule_items if start <= i.date <= end]
    items.sort(key=lambda i: (i.date, i.start_time))
    return {"items": [i.model_dump(mode="json") for i in items]}


def _free_slots_for_day(state, d: date, duration_minutes: int, day_start_min: int, day_end_min: int) -> list[str]:
    busy_items = sorted(
        (i for i in state.schedule_items if i.date == d and i.status == "planned"),
        key=lambda i: i.start_time,
    )
    busy = [
        (_to_minutes(i.start_time), _to_minutes(i.start_time) + i.duration_minutes)
        for i in busy_items
    ]

    cursor = day_start_min
    free_slots = []
    for busy_start, busy_end in busy:
        if busy_start > cursor and busy_start - cursor >= duration_minutes:
            free_slots.append(cursor)
        cursor = max(cursor, busy_end)
    if day_end_min - cursor >= duration_minutes:
        free_slots.append(cursor)

    return [_to_time_str(m) for m in free_slots]


@tool
def get_free_time(
    start_date: str,
    duration_minutes: int,
    end_date: str | None = None,
    day_start: str = "07:00",
    day_end: str = "22:00",
) -> dict:
    """Find open time slots across a date range that can fit duration_minutes.

    Checking a range of dates in one call (instead of one call per day) matters on
    rate-limited model providers -- prefer passing a wide end_date over calling this
    tool repeatedly for single days.

    Args:
        start_date: ISO date (YYYY-MM-DD) to start searching from.
        duration_minutes: How long a slot is needed, in minutes.
        end_date: ISO date (YYYY-MM-DD) to search through, inclusive. If omitted,
            only start_date is checked.
        day_start: Earliest time of day to consider (HH:MM), default 07:00.
        day_end: Latest time of day to consider (HH:MM), default 22:00.

    Returns:
        {"days": [{"date": ..., "free_start_times": [...]}, ...]} -- each free_start_times
        entry is a HH:MM time at which a slot of at least duration_minutes is open.
        Skipped schedule items don't block time.
    """
    state = load_state()
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date) if end_date else start
    day_start_min = _to_minutes(time.fromisoformat(day_start))
    day_end_min = _to_minutes(time.fromisoformat(day_end))

    days = []
    current = start
    while current <= end:
        days.append({
            "date": current.isoformat(),
            "free_start_times": _free_slots_for_day(state, current, duration_minutes, day_start_min, day_end_min),
        })
        current += timedelta(days=1)

    return {"days": days}


@tool
def create_schedule_item(
    title: str,
    date_: str,
    start_time: str,
    duration_minutes: int,
    goal_id: str | None = None,
    notes: str | None = None,
) -> dict:
    """Create a new schedule item, rejecting it if it overlaps an existing planned item.

    Call get_free_time first to find a valid slot -- this tool will not silently
    double-book, it returns an error instead.

    Args:
        title: Short activity title (e.g. "20-minute drawing session").
        date_: ISO date (YYYY-MM-DD) for the activity.
        start_time: HH:MM start time.
        duration_minutes: Length of the activity in minutes.
        goal_id: Optional id of the Goal this activity serves.
        notes: Optional free-text notes.

    Returns:
        The created schedule item, or {"error": ...} if it overlaps an existing item.
    """
    state = load_state()
    d = date.fromisoformat(date_)
    new_start = _to_minutes(time.fromisoformat(start_time))
    new_end = new_start + duration_minutes

    for existing in state.schedule_items:
        if existing.date != d or existing.status != "planned":
            continue
        existing_start = _to_minutes(existing.start_time)
        existing_end = existing_start + existing.duration_minutes
        if _overlaps(new_start, new_end, existing_start, existing_end):
            return {
                "error": f"Overlaps existing item '{existing.title}' at "
                f"{existing.start_time} on {date_}. Call get_free_time to find an open slot."
            }

    item = ScheduleItem(
        title=title,
        date=d,
        start_time=start_time,
        duration_minutes=duration_minutes,
        goal_id=goal_id,
        notes=notes,
    )
    state.schedule_items.append(item)
    save_state(state)
    return item.model_dump(mode="json")
