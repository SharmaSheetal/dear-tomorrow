"""Planner Agent -- turns the user's active goal into 2-3 small scheduled activities.

Same pattern as Goal Discovery: the LLM reasons and checks free time via tools, but the
final proposal is structured output (capped to 2-3 items by the schema itself), and
persistence to schedule items happens as a deterministic Python loop, not LLM tool calls.
"""

from datetime import date

from pydantic import BaseModel, Field
from strands import Agent, tool

from dear_tomorrow.llm.provider import get_model
from dear_tomorrow.llm.retry import call_with_retry
from dear_tomorrow.tools.goal_tools import get_active_goal
from dear_tomorrow.tools.schedule_tools import create_schedule_item, get_free_time, get_schedule

# date/start_time are plain strings, not pydantic date/time types: some providers'
# structured-output JSON schema validation enforces strict RFC3339 (requires seconds,
# e.g. "18:30:00") and rejects the natural "18:30" the model produces. Validating these
# ourselves (via create_schedule_item, which already parses HH:MM) is more robust.


class PlannedActivity(BaseModel):
    title: str = Field(description="Short activity title, e.g. '20-minute drawing session'.")
    date: str = Field(description="ISO date, e.g. 2026-09-14.")
    start_time: str = Field(description="24-hour time as HH:MM, e.g. 19:00.")
    duration_minutes: int = Field(gt=0, le=180)


class PlanProposal(BaseModel):
    """The Planner agent's structured proposal, before persistence."""

    activities: list[PlannedActivity] = Field(min_length=2, max_length=3)
    message: str = Field(description="Short summary to show the user about what was scheduled and why.")


def _build_system_prompt() -> str:
    return f"""You are the Planner specialist for Dear Tomorrow. Turn the user's active goal \
into 2-3 small, concrete scheduled activities over the next several days.

Today's date is {date.today().isoformat()}. Only schedule activities on or after today.

Before proposing, call get_schedule once for the next 5-7 days to see existing commitments, \
and get_free_time ONCE with a start_date/end_date range covering those same days to find \
genuinely open slots -- never propose a time that's already busy. Do not call get_free_time \
separately for each day; pass the whole range in one call.

Keep each activity small (typically 15-45 minutes) -- the point is an easy on-ramp, not a \
big commitment. Spread activities across different days rather than stacking them on one day.
"""


@tool
def planner_agent(context: str = "") -> dict:
    """Turn the user's current active goal into 2-3 small scheduled activities.

    Call this after a goal exists (just discovered, or already active). Reads the active
    goal and existing schedule itself -- you don't need to pass goal details in.

    Args:
        context: Optional extra detail from the conversation (e.g. stated availability
            or time preferences) to help pick good slots.

    Returns:
        {"activities": [...], "message": ...} the created schedule items and a summary
        to relay to the user, or {"error": ...} if there is no active goal.
    """
    active_goal = get_active_goal()
    if "active_goal" in active_goal:
        return {"error": "No active goal to plan for."}

    agent = Agent(
        model=get_model(),
        tools=[get_schedule, get_free_time],
        system_prompt=_build_system_prompt(),
    )
    prompt = f"Goal: {active_goal['title']} (area: {active_goal['area']}). {context}".strip()
    result = call_with_retry(lambda: agent(prompt, structured_output_model=PlanProposal))
    proposal = result.structured_output

    created_items = []
    errors = []
    for activity in proposal.activities:
        created = create_schedule_item(
            title=activity.title,
            date_=activity.date,
            start_time=activity.start_time,
            duration_minutes=activity.duration_minutes,
            goal_id=active_goal["id"],
        )
        if "error" in created:
            errors.append(created["error"])
        else:
            created_items.append(created)

    response = {"activities": created_items, "message": proposal.message}
    if errors:
        response["errors"] = errors
    return response
