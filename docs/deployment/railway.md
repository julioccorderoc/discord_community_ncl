# Deployment Guide — Railway

**Decision:** ADR-003
**Platform:** [railway.app](https://railway.app)
**Last Updated:** 2026-02-21

---

## Architecture Overview

The project deploys as **two separate Railway services** inside one Railway Project.
Both services share the same environment variables and talk to the same Supabase database.

```text
Railway Project: community-os
├── Service: bot        (Worker — no public port)
│   └── uv run python main.py
└── Service: dashboard  (Web Service — public URL)
    └── uv run streamlit run src/dashboard/app.py --server.port $PORT --server.address 0.0.0.0
```

Supabase is already hosted — it is **not** deployed through Railway.

---

## Prerequisites

Before touching Railway:

1. **Railway account** — sign up at [railway.app](https://railway.app) with your GitHub account (enables git-push deploys)
2. **GitHub repo** — the project must be pushed to a GitHub repository Railway can access
3. **All credentials ready** — have your `.env` values on hand; you will enter them in the Railway UI. See `.env.example` at the repo root for the full list.
4. **EPIC-006 complete** — `ADMIN_PASSWORD` is a required env var for the dashboard. Do not deploy before EPIC-006 is done.

---

## Step 1 — Create the Railway Project

1. Log into [railway.app](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Authorise Railway to access your GitHub organisation/account if prompted
5. Select the `discord_community_ncl` repository
6. Railway will scaffold a default service — **do not deploy yet**; rename it first (see Step 2)

---

## Step 2 — Configure the Bot Service (Worker)

This service runs the Discord bot as a persistent background process. It has no public HTTP port.

1. Click the auto-created service → **Settings**
2. **Name:** `bot`
3. **Start Command:** `uv run python main.py`
4. **Root Directory:** leave blank (project root)
5. Under **Deploy**, set **Restart Policy** to `Always` — the bot must reconnect automatically if it crashes
6. Do **not** enable a public domain for this service

---

## Step 3 — Add the Dashboard Service (Web Service)

1. In the Railway Project view, click **New** → **GitHub Repo** (same repo)
2. **Name:** `dashboard`
3. **Start Command:** `uv run streamlit run src/dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
   - `$PORT` is injected automatically by Railway — do not hardcode a port number
   - `--server.address 0.0.0.0` is required so Railway's router can reach the process
4. Under **Networking**, click **Generate Domain** to get a public URL for the dashboard

---

## Step 4 — Set Environment Variables

Environment variables are set **per service** in the Railway UI.
Both services need the full set of variables — the easiest way is to use **Shared Variables** at the Project level:

1. In the Railway Project view, click **Variables** (top-level, not inside a service)
2. Add every variable from `.env.example` with your real values:

| Variable | Required | Notes |
|---|---|---|
| `SUPABASE_URL` | Yes | From Supabase project Settings → API |
| `SUPABASE_SECRET_KEY` | Yes | Use the `service_role` key, not `anon` |
| `DISCORD_BOT_TOKEN` | Yes | From Discord Developer Portal → Bot |
| `STAFF_ROLE_ID` | No | Ticket system disabled if absent |
| `TICKET_CATEGORY_ID` | No | Tickets go to server root if absent |
| `GEMINI_API_KEY` | Yes | From Google AI Studio |
| `GEMINI_MODEL` | No | Default: `gemini-2.0-flash-lite` |
| `GEMINI_TIMEOUT_SECONDS` | No | Default: `20` |
| `ADMIN_PASSWORD` | Yes | Gate for admin section of dashboard |

1. After saving, go into each service → **Variables** → click **Reference Project Variable** for each key to inherit from the shared set

---

## Step 5 — Deploy

1. Trigger the first deploy by clicking **Deploy** in each service, or push a commit to your linked branch
2. Watch the build logs — Railway runs `uv sync` automatically (detects `pyproject.toml` and `uv.lock`)
3. Check the bot service logs for: `Bot ready: <name> (ID: <id>) | Synced X slash command(s)`
4. Check the dashboard service logs for: `You can now view your Streamlit app in your browser`
5. Open the dashboard public URL to confirm the UI loads

---

## Ongoing Deploys

Every push to the linked branch (default: `main`) triggers an automatic redeploy for both services.

- Bot service: Railway drains the old container and starts a new one — expect ~5–10 seconds of downtime per deploy
- Dashboard service: zero-downtime rolling deploy

To deploy a specific branch without merging to `main`: go to the service → **Settings** → **Source Branch** and change it temporarily.

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Bot doesn't come online | `DISCORD_BOT_TOKEN` is wrong or missing |
| Slash commands not showing in Discord | `tree.sync()` failed — check bot logs for errors on startup |
| Dashboard crashes on load | `SUPABASE_URL` or `SUPABASE_SECRET_KEY` is wrong |
| `/audit` fails with 404 | `GEMINI_MODEL` is set to a model not available for your API key — try `gemini-2.0-flash-lite` |
| `/audit` times out | Increase `GEMINI_TIMEOUT_SECONDS` or check Gemini API status |
| Admin panel not accessible | `ADMIN_PASSWORD` is not set |
| Build fails with `uv: command not found` | Railway should detect `uv` via `pyproject.toml` — check that `uv.lock` is committed |

---

## Notes

- **Never upload a `.env` file to Railway.** Use the Variables UI only.
- **`uv.lock` must be committed** to the repo — Railway uses it to reproduce exact dependency versions.
- The bot and dashboard are independent processes. You can redeploy either one without touching the other.
- Logs are available in real-time in the Railway service dashboard under **Logs**.
