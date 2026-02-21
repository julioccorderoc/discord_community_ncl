# Active Epic: EPIC-007 — Production Deployment

**Status:** Active
**Started:** 2026-02-21
**Prerequisites:** EPIC-001 ✓, EPIC-002 ✓, EPIC-003 ✓, EPIC-004 ✓, EPIC-005 ✓, EPIC-006 ✓

## Definition of Done

- [ ] `uv.lock` committed to the repository
- [ ] Railway Project created with two services: `bot` (Worker) and `dashboard` (Web Service)
- [ ] All env vars from `.env.example` configured in Railway Variables UI (Project-level Shared Variables)
- [ ] Bot service logs `Bot ready` and slash commands are visible in Discord
- [ ] Dashboard service is accessible via its Railway-generated public URL
- [ ] A push to `main` triggers an automatic redeploy of both services

## Full Runbook

All step-by-step instructions are in `docs/deployment/railway.md`. Follow that document sequentially.

## Implementation Notes

- **Two services, one project.** Railway runs the bot as a Worker (no public port) and the dashboard as a Web Service (public URL with `$PORT` injected).
- **Bot start command:** `uv run python main.py`
- **Dashboard start command:** `uv run streamlit run src/dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
- **`uv.lock` is mandatory.** Railway uses it to reproduce the exact dependency graph via `uv sync`. If it isn't committed, the build will fail.
- **Environment variables via Shared Variables.** Set all vars at the Project level in Railway, then reference them in each service — avoids duplicating secrets.
- **No `.env` upload.** Secrets live only in the Railway Variables UI.
- **Restart policy for bot:** set to `Always` so the bot reconnects automatically after crashes or deploys.

## Pre-flight Checklist (before touching Railway)

1. Confirm `uv.lock` is committed: `git ls-files uv.lock`
2. All env vars in `.env.example` are accounted for in your real `.env`
3. Code is pushed to `main` on GitHub
4. Railway account is connected to your GitHub account

## Environment Variables Reference

| Variable | Required | Source |
| --- | --- | --- |
| `SUPABASE_URL` | Yes | Supabase → Settings → API |
| `SUPABASE_SECRET_KEY` | Yes | Supabase `service_role` key |
| `DISCORD_BOT_TOKEN` | Yes | Discord Developer Portal → Bot |
| `STAFF_ROLE_ID` | No | Right-click role in Discord (Developer Mode) |
| `TICKET_CATEGORY_ID` | No | Right-click category channel |
| `GEMINI_API_KEY` | Yes | Google AI Studio |
| `GEMINI_MODEL` | No | Default: `gemini-2.0-flash-lite` |
| `GEMINI_TIMEOUT_SECONDS` | No | Default: `20` |
| `ADMIN_PASSWORD` | Yes | Your chosen admin panel password |
