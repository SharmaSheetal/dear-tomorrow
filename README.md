# Dear Tomorrow

**Give yourself something to look forward to.**

A personal adaptive AI agent that helps you find a meaningful short-term goal when you don't have one, turns it into small everyday activities, fits them into your real schedule, and adapts when your energy, mood, or plans change.

Built with [Strands Agents SDK](https://strandsagents.com/) 

## The problem

After finishing school, a job change, or any long structured pursuit, it's easy to lose the routines and sense of progress that used to give your days shape. The result: work, scrolling, overthinking, sleep, repeat. Not a lack of motivation — a lack of something worth working toward.

## What it does

1. Understands where you currently are (interests, schedule, mood, constraints).
2. Helps you discover a meaningful short-term goal when you don't have one.
3. Turns that goal into small, achievable activities.
4. Fits those activities into your existing schedule.
5. Adapts the plan when something changes — low energy, no time, a cancelled plan — instead of just marking things missed.
6. Learns what actually works for you over time.
7. Helps you see that your life is moving forward.

Core philosophy: *don't force your life to fit the schedule — adapt the schedule to your life.*

## Architecture

A small multi-agent system, not a single chatbot wrapped around an LLM:

- **Orchestrator Agent** — talks to the user, delegates to the specialists below via Strands' agents-as-tools pattern.
- **Goal Discovery Agent** — proposes one meaningful short-term goal when the user doesn't have one.
- **Planner Agent** — turns a goal into small scheduled activities, using deterministic tools for time-slot logic.

Every agent acts through real tools (read/update profile, create/read goals, read/write schedule) rather than just generating text — the loop is *understand → decide → use tool → observe result → adapt → take action*.

More agents (Activity/Well-being, Reflection/Adaptation) and features (real-world activity search, Life Momentum, weekly reflection) are planned but intentionally not built yet — see the progress tracker.

## Project status

**Phase 1 (in progress):** user context → goal discovery → activity recommendation → basic schedule creation, with mock/local data and a CLI interface. Currently at the project-scaffold stage — module structure is in place; agent, tool, and model logic are being filled in incrementally.

Progress is tracked in [`Dear_Tomorrow_Progress_Tracker.xlsx`](./Dear_Tomorrow_Progress_Tracker.xlsx) (build roadmap, open decisions, demo-story checklist, agents/tools inventory).

## Project structure

```
dear_tomorrow/
  llm/provider.py         # get_model() — swappable model provider (Groq / Gemini / Anthropic)
  models/                 # domain schemas: UserProfile, Goal, ScheduleItem
  tools/                  # deterministic tool functions the agents call
  storage/json_store.py   # JSON-file-backed state persistence
  agents/                 # orchestrator, goal_discovery, planner
  cli.py                  # Phase 1 chat interface
data/state.json           # persisted user state
```

## Tech stack

- Python 3.13, [uv](https://docs.astral.sh/uv/) for dependency management
- [Strands Agents SDK](https://strandsagents.com/) for agent orchestration and tool use
- Groq (free-tier) as the current LLM provider, behind a swappable `get_model()` abstraction
- JSON-file-backed local state for Phase 1 (no database)

## Setup

```bash
uv sync
cp .env.example .env   # fill in your API key for the provider set in MODEL_PROVIDER
uv run python main.py
```
