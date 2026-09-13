"""Phase 1 chat interface: basic input/print loop against the orchestrator.

Prints what actually changed in state.json after each turn -- goals created, activities
scheduled, mood logged -- so it's visible that the agent took real action, not just talk.
"""

from dear_tomorrow.agents.orchestrator import handle_user_message
from dear_tomorrow.storage.json_store import AppState, load_state


def _print_state_changes(before: AppState, after: AppState) -> None:
    before_goal_ids = {g.id for g in before.goals}
    for g in after.goals:
        if g.id not in before_goal_ids:
            print(f"  [goal created] {g.title} ({g.area})")

    before_item_ids = {i.id for i in before.schedule_items}
    new_items = [i for i in after.schedule_items if i.id not in before_item_ids]
    for item in sorted(new_items, key=lambda i: (i.date, i.start_time)):
        print(f"  [scheduled] {item.date} {item.start_time} - {item.title} ({item.duration_minutes} min)")

    before_mood_count = len(before.user_profile.mood_log) if before.user_profile else 0
    after_mood_count = len(after.user_profile.mood_log) if after.user_profile else 0
    if after.user_profile and after_mood_count > before_mood_count:
        latest = after.user_profile.mood_log[-1]
        energy_note = f" (energy: {latest.energy})" if latest.energy else ""
        print(f"  [mood logged] {latest.mood}{energy_note}")


def main() -> None:
    print("Dear Tomorrow -- give yourself something to look forward to.")
    print("Type 'quit' or 'exit' to leave.\n")

    while True:
        try:
            user_message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSee you tomorrow.")
            break

        if not user_message:
            continue
        if user_message.lower() in {"quit", "exit"}:
            print("See you tomorrow.")
            break

        before = load_state()
        reply = handle_user_message(user_message)
        after = load_state()

        print(f"\nDear Tomorrow: {reply}\n")
        _print_state_changes(before, after)
        print()


if __name__ == "__main__":
    main()
