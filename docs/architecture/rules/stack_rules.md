# STACK RULES

Extracted from **ADR-001** (Unified Python Stack). These are hard constraints for all agents working on this project.

---

## 1. Language & Runtime

- ALL code is **Python 3.13+**. Never introduce Node.js, TypeScript, or any non-Python runtime.
- Dependency management uses **`uv`** (see `pyproject.toml`). Never use `pip install` directly; use `uv add`.
- Python version is pinned in `.python-version`. Do not change it without a new ADR.

---

## 2. Bot Layer (`src/cogs/`)

- The Discord bot is built exclusively with **`discord.py`** (asyncio). Do not use `hikari`, `nextcord`, or any other Discord library.
- Bot logic is split into **Cogs** — one Cog per domain (e.g., `activity.py`, `tickets.py`). Never put all commands in a single file.
- Slash commands use the `@app_commands.command()` decorator. Prefix commands (`!ping`) are only allowed for health-check/admin utilities.
- Event listeners use `@commands.Cog.listener()`. Every listener must be `async`.
- **Never block the event loop.** Use `await asyncio.sleep()`, never `time.sleep()`. Wrap any synchronous I/O with `asyncio.to_thread()`.

---

## 3. Dashboard Layer (`src/dashboard/`)

- The dashboard is built exclusively with **Streamlit**. Do NOT use Flask, FastAPI, Django, or any other web framework.
- Use `@st.cache_data(ttl=60)` on every function that fetches from the database to prevent redundant calls on each Streamlit re-run.
- The dashboard is **internal-only**. Do NOT implement public auth flows, OAuth, or JWT. The only "gate" is the Admin Mode password (see PRD §4).
- Streamlit is synchronous. Do NOT use `asyncio.run()` or `await` inside dashboard scripts. If a utility in `src/` is async, create a sync wrapper for the dashboard's use.

---

## 4. Shared Layer (`src/models/`, `src/database/`, `src/config.py`)

- **Pydantic V2 models** in `src/models/schemas.py` are the single source of truth for data shapes. Both the bot and dashboard import from here.
- **Never** duplicate a Pydantic model definition — one definition, many imports.
- **Config:** All environment variables are loaded via `src/config.py` using `python-dotenv`. Both bot and dashboard use this single config object. Never hardcode credentials.
- **Database client:** The Supabase client is initialized once in `src/database/client.py` and imported wherever needed.

---

## 5. Async / Sync Boundary Rules

| Context | Rule |
| --- | --- |
| Bot (discord.py) | Fully async. All functions touching Discord or DB must be `async def`. |
| Dashboard (Streamlit) | Fully sync. Call sync service functions only. |
| `src/services/` | Sync wrappers around async logic for dashboard consumption. |

---

## 6. Forbidden Patterns

| Pattern | Why Forbidden |
| --- | --- |
| `import sqlalchemy` / `import tortoise` | No ORMs — see ADR-002 |
| `time.sleep(n)` in async context | Blocks the event loop |
| `f"SELECT ... WHERE id={user_id}"` | SQL injection risk — see db_rules.md §2 |
| `supabase.table(...)` inside `src/dashboard/` | Violates service layer — see db_rules.md §3 |
| JS frameworks (React/Vue/Next) | Python-only stack per ADR-001 |
| Hardcoded API keys or tokens in source | Use `src/config.py` + `.env` only |
