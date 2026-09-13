"""Tools for reading/creating the user's goal.

Phase 1 enforces a single active goal at a time -- create_goal refuses to create a
second one. Goal evolution (updating, abandoning) is a Phase 2+ feature.
"""

from strands import tool

from dear_tomorrow.models.goal import Goal
from dear_tomorrow.storage.json_store import load_state, save_state


@tool
def get_active_goal() -> dict:
    """Return the user's current active goal, if any.

    Returns:
        {"active_goal": null} if the user has no active goal, otherwise the goal itself.
    """
    state = load_state()
    active = next((g for g in state.goals if g.status == "active"), None)
    if active is None:
        return {"active_goal": None}
    return active.model_dump(mode="json")


@tool
def create_goal(title: str, area: str, notes: str | None = None) -> dict:
    """Create a new active goal for the user. Refuses if an active goal already exists.

    Args:
        title: Short, concrete goal title (e.g. "30-day drawing challenge").
        area: One of: learning, creativity, fitness, social, exploration, hobby,
            personal_project, career, independence.
        notes: Optional context for why this goal was chosen.

    Returns:
        The created goal, or {"error": ...} if an active goal already exists.
    """
    state = load_state()
    if any(g.status == "active" for g in state.goals):
        return {
            "error": "An active goal already exists. Call get_active_goal to see it "
            "before proposing a new one."
        }
    goal = Goal(title=title, area=area, notes=notes)
    state.goals.append(goal)
    save_state(state)
    return goal.model_dump(mode="json")
