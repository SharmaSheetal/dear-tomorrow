"""Tools for reading/updating the user's profile and logging mood."""

from strands import tool

from dear_tomorrow.models.user import MoodEntry, UserProfile
from dear_tomorrow.storage.json_store import load_state, save_state


@tool
def get_user_profile() -> dict:
    """Return the current user's profile: name, interests, constraints, and mood history.

    Returns:
        The user's profile, or {"error": ...} if no profile has been created yet.
    """
    state = load_state()
    if state.user_profile is None:
        return {"error": "No user profile exists yet. Call update_user_profile with a name to create one."}
    return state.user_profile.model_dump(mode="json")


@tool
def update_user_profile(
    name: str | None = None,
    interests: list[str] | None = None,
    constraints: list[str] | None = None,
) -> dict:
    """Update the user's profile. Only the fields you provide are changed. Creates the profile if none exists yet.

    Args:
        name: The user's name. Required if no profile exists yet.
        interests: Full replacement list of the user's interests (e.g. ["drawing", "hiking"]).
        constraints: Full replacement list of the user's constraints (e.g. ["no mornings", "budget-conscious"]).

    Returns:
        The updated profile, or {"error": ...} if no profile exists and no name was given.
    """
    state = load_state()
    if state.user_profile is None:
        if name is None:
            return {"error": "No profile exists yet; provide `name` to create one."}
        state.user_profile = UserProfile(
            name=name,
            interests=interests or [],
            constraints=constraints or [],
        )
    else:
        if name is not None:
            state.user_profile.name = name
        if interests is not None:
            state.user_profile.interests = interests
        if constraints is not None:
            state.user_profile.constraints = constraints
    save_state(state)
    return state.user_profile.model_dump(mode="json")


@tool
def log_mood(mood: str, energy: str | None = None, note: str | None = None) -> dict:
    """Append an entry to the user's mood log. This is a history, not a snapshot -- past entries are kept.

    Args:
        mood: A short description of how the user feels (e.g. "exhausted", "excited", "bored").
        energy: One of "low", "medium", "high", if known.
        note: Optional free-text context (e.g. "long day at work").

    Returns:
        The logged entry, or {"error": ...} if no user profile exists yet.
    """
    state = load_state()
    if state.user_profile is None:
        return {"error": "No user profile exists yet -- call update_user_profile first."}
    entry = MoodEntry(mood=mood, energy=energy, note=note)
    state.user_profile.mood_log.append(entry)
    save_state(state)
    return entry.model_dump(mode="json")
