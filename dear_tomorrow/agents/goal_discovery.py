"""Goal Discovery Agent -- proposes exactly one short-term goal when the user has none.

Structured output produces a lightweight GoalProposal (not the full persisted Goal --
id/status/created_date are storage concerns the LLM shouldn't have to invent). The tool
wrapper then deterministically calls create_goal() in plain Python, rather than trusting
the LLM to invoke that tool correctly itself.
"""

from pydantic import BaseModel, Field
from strands import Agent, tool

from dear_tomorrow.llm.provider import get_model
from dear_tomorrow.llm.retry import call_with_retry
from dear_tomorrow.models.goal import GoalArea
from dear_tomorrow.tools.goal_tools import create_goal
from dear_tomorrow.tools.profile_tools import get_user_profile

SYSTEM_PROMPT = """You are the Goal Discovery specialist for Dear Tomorrow, an agent that \
helps people who feel directionless find something meaningful to work toward.

Call get_user_profile to learn the user's interests and constraints before proposing anything.

Propose exactly ONE small, concrete, short-term goal -- never a list of options. \
Overwhelming the user with choices defeats the point. Ground the goal in something from \
their actual interests/mood when possible. Frame it as a low-commitment experiment (e.g. \
"a 30-day drawing challenge"), not a life plan.

area must be one of: learning, creativity, fitness, social, exploration, hobby, \
personal_project, career, independence.

reasoning should be 1-3 sentences, written directly to the user, explaining why this fits \
them right now -- this text will be shown to them as-is.
"""


class GoalProposal(BaseModel):
    """The Goal Discovery agent's structured proposal, before persistence."""

    title: str = Field(description="Short, concrete goal title, e.g. '30-day drawing challenge'.")
    area: GoalArea
    reasoning: str = Field(description="1-3 sentences pitched directly to the user.")


@tool
def goal_discovery_agent(user_message: str) -> dict:
    """Propose and create a single new goal for a user who has none.

    Only call this after get_active_goal() has confirmed the user has no active goal.
    Reads the user's profile, proposes one goal, and persists it via create_goal.

    Args:
        user_message: What the user said that indicates they want/need a new goal
            (e.g. "I don't have a goal right now, I feel like I'm wasting my evenings").

    Returns:
        The created Goal plus "reasoning" (the pitch to relay to the user), or
        {"error": ...} if a goal could not be created (e.g. one already exists).
    """
    agent = Agent(model=get_model(), tools=[get_user_profile], system_prompt=SYSTEM_PROMPT)
    result = call_with_retry(lambda: agent(user_message, structured_output_model=GoalProposal))
    proposal = result.structured_output

    created = create_goal(title=proposal.title, area=proposal.area, notes=proposal.reasoning)
    if "error" in created:
        return created

    return {**created, "reasoning": proposal.reasoning}
