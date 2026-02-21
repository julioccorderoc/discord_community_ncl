# PROJECT STRUCTURE RULES

This document is the authoritative reference for where code lives. Agents must not create files outside these boundaries without a new ADR.

---

## 1. Repository Layout

```text
discord_community_ncl/
├── .ai/                        # Agent working memory (plans, errors)
├── database/                   # SQL-only. No Python here.
│   ├── table_initial_setup.sql # Schema definition (source of truth)
│   ├── row_level_security.sql  # RLS policies
│   └── seed_test_data.sql      # Dev/test fixtures
├── docs/
│   ├── PRD.md                  # Product requirements (do not modify without PM approval)
│   ├── roadmap.md              # Epic tracker (Planner Agent writes here)
│   └── architecture/
│       ├── ADRs/               # Immutable decision records
│       └── rules/              # Injected agent constraints (this file lives here)
├── src/                        # ALL application Python code
│   ├── cogs/                   # discord.py Cogs (bot commands & event listeners)
│   ├── database/               # Supabase client singleton
│   ├── models/                 # Pydantic V2 schemas (shared by bot + dashboard)
│   ├── services/               # Business logic / DB query layer (shared by bot + dashboard)
│   └── config.py               # Env var loading via python-dotenv
├── main.py                     # Bot entry point
├── pyproject.toml              # Dependencies (managed by uv)
└── .env                        # Local secrets — NEVER commit to git
```

---

## 2. Placement Rules

| What you are building | Where it goes |
| --- | --- |
| New Discord command or event listener | `src/cogs/<domain>.py` |
| Supabase query / business logic | `src/services/<domain>_service.py` |
| Pydantic model or enum | `src/models/schemas.py` |
| Streamlit page or widget | `src/dashboard/<page>.py` (create dir when EPIC-004 begins) |
| New env variable | `.env` + document in `src/config.py` |
| Schema change | `database/table_initial_setup.sql` + matching Pydantic update |
| One-off SQL migration | New file in `database/` with a descriptive name |

---

## 3. Naming Conventions

- **Files:** `snake_case.py`
- **Cog classes:** `PascalCase` extending `commands.Cog`
- **Service functions:** `snake_case`, verb-first (e.g., `get_rising_stars`, `create_ticket`, `log_activity`)
- **Pydantic models:** `PascalCase` matching the DB table concept (e.g., `DiscordUser`, `Ticket`)
- **Constants / config fields:** `SCREAMING_SNAKE_CASE`

---

## 4. What Does NOT Belong in `src/`

- Raw SQL strings (use `supabase.table(...)` or Stored Procedures)
- Hardcoded Discord IDs, channel IDs, or role IDs (use `src/config.py`)
- Any file larger than ~300 lines — split into sub-modules instead
