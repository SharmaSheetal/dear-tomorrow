"""Orchestrator Agent -- the agent the user actually talks to.

Whether an active goal exists is checked deterministically in Python before the LLM is
invoked, and the answer is baked into the system prompt -- routing between Goal Discovery
and Planner doesn't depend on the model remembering to check first. The LLM decides HOW
to respond and WHEN to delegate within that known state, not whether a goal exists.

Each call is a fresh, stateless Agent invocation -- conversation memory isn't persisted
across turns. State that matters (profile, goals, schedule) already persists via the
JSON store; adding conversation memory on top is unneeded complexity for Phase 1.
"""

from strands import Agent

from dear_tomorrow.agents.goal_discovery import goal_discovery_agent
from dear_tomorrow.agents.planner import planner_agent
from dear_tomorrow.llm.provider import get_model
from dear_tomorrow.llm.retry import call_with_retry
from dear_tomorrow.tools.goal_tools import get_active_goal
from dear_tomorrow.tools.profile_tools import get_user_profile, log_mood, update_user_profile
from dear_tomorrow.tools.schedule_tools import get_schedule


def _build_system_prompt(has_active_goal: bool) -> str:
    goal_state = (
        "The user ALREADY has an active goal. If they need activities scheduled for it, "
        "call planner_agent. Do not call goal_discovery_agent -- it will refuse since a "
        "goal already exists."
        if has_active_goal
        else "The user has NO active goal yet. If their message suggests they want one "
        "(feeling directionless, bored, wanting something to work toward), call "
        "goal_discovery_agent. It will propose exactly one goal and create it."
    )

    return f"""You are Dear Tomorrow, a personal agent that helps people find something \
meaningful to work toward and turns it into small everyday activities. Your philosophy: \
don't force someone's life to fit a schedule, adapt the schedule to their life.

{goal_state}

Use log_mood to record how the user says they're feeling, when they mention it. Use \
get_user_profile / update_user_profile to learn about or update their interests and \
constraints. Use get_schedule if they ask what's already planned.

After goal_discovery_agent creates a goal, immediately call planner_agent next in the \
same turn so the goal turns into real scheduled activities -- don't stop at just the goal.

Speak directly to the user in a warm, concise voice. Never mention tool names or internal \
mechanics to them.
"""


def handle_user_message(user_message: str) -> str:
    """Handle one user turn: route to the right specialists, return a reply to show them."""
    active = get_active_goal()
    has_active_goal = "active_goal" not in active

    agent = Agent(
        model=get_model(),
        tools=[
            get_user_profile,
            update_user_profile,
            log_mood,
            get_schedule,
            goal_discovery_agent,
            planner_agent,
        ],
        system_prompt=_build_system_prompt(has_active_goal),
    )
    result = call_with_retry(lambda: agent(user_message))
    return str(result)
