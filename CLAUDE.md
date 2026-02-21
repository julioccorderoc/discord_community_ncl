# Community OS — Claude Working Guide

## Project Overview

Discord community management "Operating System" for NCL. A `discord.py` bot tracks member engagement and a Streamlit internal dashboard surfaces insights for Creator Managers. All Python, no JavaScript.

## Critical Rules — Read Before Writing Code

| Rule File | Covers |
| --- | --- |
| `docs/architecture/rules/stack_rules.md` | Language, bot layer, dashboard layer, forbidden patterns |
| `docs/architecture/rules/db_rules.md` | Supabase client usage, SQL injection protocol, service layer |
| `docs/architecture/rules/project_structure.md` | Where every file type lives, naming conventions |

**ADRs** in `docs/architecture/ADRs/` are immutable decision records — read them for context, never modify them.

## Current Epic Status

See `docs/roadmap.md`. Check the active Epic and its Definition of Done before starting any task. Use the `planner` agent to advance the roadmap.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.13+ |
| Package manager | `uv` (use `uv add`, never `pip install`) |
| Bot | `discord.py` (asyncio) |
| Dashboard | Streamlit |
| Database | Supabase (PostgREST client — no ORM) |
| Models | Pydantic V2 |
| Config | `python-dotenv` via `src/config.py` |

## Directory Quick Reference

```text
src/cogs/          → Discord bot commands & event listeners (one Cog per domain)
src/database/      → Supabase client singleton (import, don't re-instantiate)
src/models/        → Pydantic V2 schemas — single source of truth for data shapes
src/services/      → Business logic & DB queries (shared by bot and dashboard)
src/config.py      → All env var loading

database/table_initial_setup.sql   → Fresh-environment schema (source of truth)
database/migration_*.sql           → Incremental changes for running instances
```

## Database Schema

| Table | Key Columns |
| --- | --- |
| `discord_users` | `discord_id` (PK, BIGINT), `guild_join_date` (for Rising Stars filter) |
| `activity_logs` | `user_id`, `type` (enum), `points_value` (pre-calculated) |
| `tickets` | `discord_channel_id` (UNIQUE — links to Discord private channel) |
| `ticket_events` | Conversation + audit trail per ticket |
| `ai_audit_logs` | LLM cost and compliance tracking |

## Engagement Score Formula

```text
Score = (Messages × 1) + (Reactions × 0.5)
```

Calculated by summing `points_value` from `activity_logs`. **Voice tracking is OUT OF SCOPE for MVP.**

## Available Agents

| Agent | When to Use |
| --- | --- |
| `planner` | Manage roadmap, activate/complete epics, check DoD |
| `bot-dev` | Discord bot features — Cogs, commands, event listeners |
| `dashboard-dev` | Streamlit UI, charts, service layer functions |
| `db-architect` | Schema changes (SQL + Pydantic models), complex queries |
| `qa` | Validate DoD, write/run tests, check regressions |

## Hard "Never Do" List

1. Never use an ORM (`sqlalchemy`, `tortoise`, etc.)
2. Never construct SQL with f-strings or `.format()` — use parameterized client methods
3. Never call `supabase.table(...)` inside `src/dashboard/` — use a service function
4. Never use `time.sleep()` in async bot code — use `await asyncio.sleep()`
5. Never hardcode Discord IDs, tokens, or passwords — use `src/config.py` + `.env`
6. Never run `pip install` — use `uv add` to keep `uv.lock` in sync
7. Never modify `docs/PRD.md` without PM approval
8. Never modify files in `docs/architecture/ADRs/` — they are immutable

## Before Starting Any Task

1. Check `docs/roadmap.md` — what Epic is active? What is the DoD?
2. Check `.ai/CURRENT_PLAN.MD` — is there in-progress work to continue?
3. Check `.ai/ERRORS.MD` — any known blockers or failure patterns?
4. Read the relevant source files **before** modifying them.
