# Community OS — NCL

An internal operating system for the NCL Discord community. A Discord bot tracks member engagement and a Streamlit dashboard surfaces insights for Creator Managers — all in Python, no JavaScript.

## What it does

| Feature | How |
| --- | --- |
| Engagement tracking | Bot listens to `on_message` and `on_reaction_add` and scores every event |
| Rising Stars & Churn Risks | Dashboard surfaces top members and those going silent |
| Ticket system | Members open private support channels via a button; staff close them with `!close` |
| AI compliance audit | `/audit` sends any text to Gemini for a Green / Yellow / Red risk assessment |
| Admin panel | Password-gated tab with health checks, AI cost ledger, and live log stream |

## Tech stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.13+ |
| Package manager | `uv` |
| Bot | `discord.py` (asyncio) |
| Dashboard | Streamlit |
| Database | Supabase (PostgREST — no ORM) |
| AI | Google Gemini (`google-genai`) |
| Models | Pydantic V2 |
| Hosting | Railway (two services: bot + dashboard) |

## Project structure

```text
src/
├── cogs/           Discord bot commands & event listeners (one Cog per domain)
├── database/       Supabase client singleton
├── models/         Pydantic V2 schemas — single source of truth for data shapes
├── services/       Business logic & DB queries (shared by bot and dashboard)
├── dashboard/      Streamlit app
└── config.py       All env var loading

database/
├── table_initial_setup.sql   Fresh-environment schema
└── migration_*.sql           Incremental changes for running instances

docs/
├── architecture/   ADRs and coding rules
├── deployment/     Railway runbook
└── roadmap.md      Epic ledger and backlog
```

## Local setup

**Prerequisites:** Python 3.13+, `uv`, a Supabase project, a Discord application, a Google AI Studio API key.

```bash
# 1. Clone and install dependencies
git clone <repo-url>
cd discord_community_ncl
uv sync

# 2. Configure environment
cp .env.example .env
# Fill in all values in .env

# 3. Apply the database schema
# Run database/table_initial_setup.sql in the Supabase SQL Editor

# 4. Start the bot (Terminal 1)
uv run python main.py

# 5. Start the dashboard (Terminal 2)
uv run streamlit run src/dashboard/app.py
```

The dashboard opens at `http://localhost:8501`.

## Environment variables

See `.env.example` at the repo root for the full list with descriptions. Required variables:

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SECRET_KEY` | Supabase `service_role` key |
| `DISCORD_BOT_TOKEN` | Bot token from Discord Developer Portal |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `ADMIN_PASSWORD` | Password for the dashboard admin tab |

## Deployment

The project runs as two Railway services in a single Railway project. See [docs/deployment/railway.md](docs/deployment/railway.md) for the full step-by-step runbook.

| Service | Type | Start command |
| --- | --- | --- |
| `bot` | Worker (no public port) | `uv run python main.py` |
| `dashboard` | Web Service (public URL) | `uv run streamlit run src/dashboard/app.py --server.port $PORT --server.address 0.0.0.0` |

Every push to `main` triggers an automatic redeploy of both services.

## Engagement score formula

```text
Score = (Messages × 1) + (Reactions × 0.5)
```

Calculated at query time by summing `points_value` from `activity_logs`. Voice tracking is out of scope for MVP.

## Docs

| Document | Purpose |
| --- | --- |
| [docs/roadmap.md](docs/roadmap.md) | Epic ledger, current status, post-MVP backlog |
| [docs/deployment/railway.md](docs/deployment/railway.md) | Railway setup runbook |
| [docs/architecture/ADRs/](docs/architecture/ADRs/) | Immutable decision records |
| [docs/architecture/rules/](docs/architecture/rules/) | Coding rules (stack, DB, project structure) |
| [.ai/ERRORS.MD](.ai/ERRORS.MD) | Known bugs and gotchas |
