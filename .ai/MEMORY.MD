# Agent Memory — Community OS

Stable facts every session should know. Consult before starting any task.

---

## Architecture

- Two processes: **bot** (`main.py`) and **dashboard** (`src/dashboard/app.py`) — both share Supabase, neither knows about the other
- Bot is fully async (discord.py). Dashboard is fully sync (Streamlit). Never mix.
- All DB calls go through `src/services/`. Never call `supabase.table()` directly in Cogs or dashboard pages.
- All env vars load through `src/config.py`. Never read `os.environ` elsewhere.
- Adding a new env var requires three files: `.env`, `src/config.py`, and `.env.example`.

## Deployment

- Platform: Railway (ADR-003). Two services: `bot` (Worker) and `dashboard` (Web Service).
- Bot start: `uv run python main.py`
- Dashboard start: `uv run streamlit run src/dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
- `uv.lock` must be committed — Railway uses it. Never delete it.
- Secrets go in Railway Variables UI only. Never upload `.env`.
- Full runbook: `docs/deployment/railway.md`

## Gemini (google-genai)

- Package: `google-genai` (NOT the deprecated `google-generativeai`)
- Import: `from google import genai` / `from google.genai import types`
- Client is a module-level singleton in `src/services/ai_service.py` — not instantiated per call
- Default model: `gemini-2.0-flash-lite` (available to new API accounts via v1beta)
- `gemini-1.5-flash` and `gemini-2.0-flash` both 404 on new accounts — see `.ai/ERRORS.MD`
- Model is configurable via `GEMINI_MODEL` env var — never hardcode it

## Discord Slash Commands

- Always `await interaction.response.defer(ephemeral=True)` at the top of every slash handler
- Always wrap the handler body in `try/except Exception` and call `interaction.followup.send()` in the except block — unhandled exceptions leave Discord stuck on "thinking..." forever
- `bot.tree.sync()` is called in `on_ready` — slash commands register globally on every startup

## Package Management

- `uv` only. Never `pip install`. Use `uv add <package>` to add dependencies.
