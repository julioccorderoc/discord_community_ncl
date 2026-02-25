# ROADMAP: COMMUNITY OS

* **Version:** 0.1.0
* **Last Updated:** 2026-02-21
* **Primary Human Owner:** Technical Architect

## Operating Rules for the Planner Agent

1. You may only move one Epic to `Active` at a time.
2. Before marking an Epic `Complete`, you must verify all its Success Criteria are met in the main branch.
3. Do not parse or extract Epics that depend on incomplete prerequisites.

---

## Epic Ledger

### EPIC-001: Infrastructure & Data Foundation (Day 0)

* **Status:** Complete
* **Dependencies:** None
* **Business Objective:** Establish the "Central Nervous System" and database connectivity.
* **Technical Boundary:** Repository setup, Docker (optional), Supabase Project Init.
* **Verification Criteria (Definition of Done):**
  * Monorepo structure created (`src/cogs`, `src/database`, `src/models`, `src/services`).
  * Supabase Table Definitions applied: `discord_users`, `activity_logs`, `tickets`, `ticket_events`, `ai_audit_logs`.
  * Bot connects to Discord Gateway and responds to `!ping`.
  * CI/CD pipeline (GitHub Actions) runs Pydantic tests.

### EPIC-002: The Engagement Engine

* **Status:** Complete
* **Dependencies:** EPIC-001
* **Business Objective:** Begin tracking user value to identify "Rising Stars."
* **Technical Boundary:** Discord Event Listeners, SQL Write Operations.
* **Verification Criteria (Definition of Done):**
  * Listener created for `on_message` and `on_reaction_add`.
  * Algorithm implemented: `Score = (Messages × 1) + (Reactions × 0.5)`. Voice tracking is deferred post-MVP.
  * Data persists to `activity_logs` table in Supabase (score is summed per user at query time).
  * Unit tests verify score calculation logic.

### EPIC-003: Ticket System Core

* **Status:** Complete
* **Dependencies:** EPIC-001, EPIC-002
* **Business Objective:** structured support channel to replace DMs.
* **Technical Boundary:** Discord Views (Buttons), Private Channel Management.
* **Verification Criteria (Definition of Done):**
  * User can click "Open Ticket" button.
  * Bot creates private channel visible only to User + Staff.
  * Ticket entry created in DB with status `OPEN`.
  * `!close` command archives the channel and updates DB status to `RESOLVED`.

### EPIC-004: Manager Dashboard (MVP)

* **Status:** Complete
* **Dependencies:** EPIC-002, EPIC-003
* **Business Objective:** Visual interface for non-technical staff.
* **Technical Boundary:** Streamlit, Pandas, Plotly.
* **Verification Criteria (Definition of Done):**
  * Streamlit app connects to Supabase using `supabase-py`.
  * **Configuration:** Implemented `python-dotenv` to load API keys from a single `.env` file at the project root (Compatible with both Bot and Dashboard).
  * **Tab 1:** "Impact Pulse" - Line chart showing engagement score vs. previous week.
  * **Tab 2:** "The Lists" - Tables for "Churn Risks" and "Rising Stars."

### EPIC-005: AI Audit & Safety

* **Status:** Complete
* **Dependencies:** EPIC-003
* **Business Objective:** Reduce risk of toxic interactions and ensure compliance.
* **Technical Boundary:** Google Gemini API (`google-genai`), Discord slash commands.
* **Verification Criteria (Definition of Done):**
  * `/audit text: <text>` slash command — staff pastes any text for analysis.
  * Gemini processes text and returns a structured risk assessment (Green / Yellow / Red).
  * Response rendered as a color-coded Discord embed with a 2–3 sentence summary.
  * Configurable model (`GEMINI_MODEL`) and timeout (`GEMINI_TIMEOUT_SECONDS`) via `.env`.
  * Token / cost logging deferred — `ai_audit_logs` table reserved for **EPIC-006**.

### EPIC-006: Admin Dashboard & Observability

* **Status:** Complete
* **Dependencies:** EPIC-004, EPIC-005
* **Business Objective:** Give the System Administrator full operational control and cost visibility without SSH access.
* **Technical Boundary:** Streamlit Admin Tab, Supabase health ping, bot process signal handling.
* **Verification Criteria (Definition of Done):**
  * **Admin Mode Toggle:** Password-gated view (simple `st.text_input` comparison against env var `ADMIN_PASSWORD`). Not an auth system — internal tool only.
  * **Health Check Panel:** Green/Red indicators for Discord Gateway, Supabase connection, and AI API reachability.
  * **Cost Ledger:** Running total of AI token costs for the current billing cycle, sourced from `ai_audit_logs`. Write to `ai_audit_logs` on every `/audit` call (tokens used, processing time, model name).
  * **Panic Button:** "Flush Cache" clears `st.cache_data`; "Stop Bot" sends a shutdown signal (implementation TBD based on deployment model).
  * **Log Stream:** Last 50 entries from `ai_audit_logs` displayed in a live-refresh table.

### EPIC-007: Production Deployment

* **Status:** Complete
* **Dependencies:** EPIC-006
* **Business Objective:** Make the bot and dashboard available 24/7 without running on a local machine.
* **Technical Boundary:** Railway (see ADR-003 and `docs/deployment/railway.md`).
* **Verification Criteria (Definition of Done):**
  * Railway Project created with two services: `bot` (Worker) and `dashboard` (Web Service)
  * All environment variables from `.env.example` configured in Railway Variables UI
  * Bot service logs `Bot ready` and slash commands are visible in Discord
  * Dashboard service is accessible via its Railway-generated public URL
  * A push to `main` triggers an automatic redeploy of both services
  * `uv.lock` is committed to the repository

---

## Post-MVP Backlog

The following are candidate epics for the next development cycle, ordered by impact.
None are Active — choose one and move it to `Active` when ready.

### EPIC-008: Ticket Intelligence (AI triage)

* **Status:** Pending
* **Dependencies:** EPIC-005, EPIC-007
* **Business Objective:** Reduce staff response time by auto-classifying and routing tickets on creation.
* **Candidate Features:**
  * On ticket creation, run the subject through Gemini and auto-set `priority` (LOW / MEDIUM / HIGH / CRITICAL)
  * Post a suggested response template in the private channel as a staff-only message
  * Add a "Ticket Summary" command (`/ticket-summary`) that summarises the full conversation thread

### EPIC-009: Engagement Leaderboard & Member Recognition

* **Status:** Pending
* **Dependencies:** EPIC-002, EPIC-007
* **Business Objective:** Motivate member participation through visible recognition.
* **Candidate Features:**
  * `/leaderboard` slash command — top 10 members by score, posted as a Discord embed
  * Scheduled weekly leaderboard post to a designated channel (configurable via env var)
  * Auto-assign a "Rising Star" role to members who break a configurable score threshold

### EPIC-010: Onboarding Flow

* **Status:** Pending
* **Dependencies:** EPIC-001, EPIC-007
* **Business Objective:** Reduce drop-off for new members in the first 7 days.
* **Candidate Features:**
  * `on_member_join` listener sends a DM with a welcome message and server guide
  * "Getting Started" checklist channel post, auto-deleted after 7 days
  * Dashboard filter: "New Members" — joined in the last 7 days, zero activity

---

### EPIC-011: Member Lifecycle Tracking (Join / Leave)

* **Status:** Complete
* **Dependencies:** EPIC-001, EPIC-007
* **Business Objective:** Know exactly when members enter and leave the community so growth trends are measurable without relying on message activity as a proxy.

#### EPIC-011 — Technical Scope

New DB table — `member_events` (migration file required):

```sql
CREATE TABLE member_events (
    id         BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES discord_users(discord_id) ON DELETE CASCADE,
    event_type VARCHAR(10) NOT NULL CHECK (event_type IN ('join', 'leave')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_member_events_user ON member_events(user_id);
CREATE INDEX idx_member_events_date ON member_events USING BRIN(created_at);
```

> **Why a new table, not extending `activity_logs`?** Join/leave events have no `channel_id` and no score weight — they are lifecycle events, not engagement events. Forcing them into `activity_logs` would require a nullable `channel_id` (breaks NOT NULL) or a meaningless sentinel. A dedicated table is cleaner and easier to query independently.

New Pydantic model — `MemberEvent` and `MemberEventType` in `src/models/schemas.py`:

```python
class MemberEventType(str, Enum):
    JOIN  = 'join'
    LEAVE = 'leave'

class MemberEvent(CommunityBaseModel):
    id:         Optional[int]
    user_id:    int
    event_type: MemberEventType
    created_at: Optional[datetime]
```

New service function in `src/services/activity_service.py`:

```python
def log_member_event(user_id: int, event_type: MemberEventType) -> None:
    supabase.table("member_events").insert({
        "user_id": user_id,
        "event_type": event_type.value,
    }).execute()
```

New listeners in `src/cogs/activity.py`:

* `on_member_join(member)` — upsert user → `log_member_event(JOIN)`
* `on_member_remove(member)` — upsert user (best-effort) → `log_member_event(LEAVE)`

> Note: `intents.members = True` is **already set** in `main.py` — no intent changes required.

#### EPIC-011 — Definition of Done

* [ ] Migration SQL created and applied to Supabase (`database/migration_002_member_events.sql`)
* [ ] `MemberEvent` and `MemberEventType` added to `src/models/schemas.py`
* [ ] `log_member_event()` added to `src/services/activity_service.py`
* [ ] `on_member_join` and `on_member_remove` listeners added to `ActivityCog`
* [ ] A test join + manual leave writes rows to `member_events` visible in Supabase
* [ ] Existing `on_message` and `on_reaction_add` behaviour is unchanged (regression check)

---

### EPIC-012: Presence & Online Session Tracking

* **Status:** Complete
* **Dependencies:** EPIC-011
* **Business Objective:** Track how long members are actively present in the server (online/idle/dnd) so Community Managers can identify truly engaged members vs. message-only participants.

#### EPIC-012 — Technical Scope

Discord Developer Portal prerequisite: enable the **Presence Intent** toggle in the Bot settings page. For a single-server bot this is a checkbox — no Discord approval process required.

Change in `main.py`:

```python
intents.presences = True   # add alongside existing intents
```

New DB table — `presence_sessions` (migration file required):

```sql
CREATE TABLE presence_sessions (
    id               BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id          BIGINT NOT NULL REFERENCES discord_users(discord_id) ON DELETE CASCADE,
    status           VARCHAR(10) NOT NULL,  -- 'online', 'idle', 'dnd'
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at         TIMESTAMPTZ,           -- NULL = session still open
    duration_seconds INT                    -- computed and written when session closes
);
CREATE INDEX idx_presence_sessions_user   ON presence_sessions(user_id);
CREATE INDEX idx_presence_sessions_active ON presence_sessions(ended_at) WHERE ended_at IS NULL;
CREATE INDEX idx_presence_sessions_date   ON presence_sessions USING BRIN(started_at);
```

New file `src/services/presence_service.py`:

```python
def open_presence_session(user_id: int, status: str) -> None: ...
def close_presence_session(user_id: int) -> None: ...       # sets ended_at + duration_seconds
def close_all_open_sessions() -> None: ...                  # called on bot startup
```

New Cog `src/cogs/presence.py` — `on_presence_update(before, after)` logic:

```text
if after.status == offline:
    close_presence_session(user_id)

elif before.status == offline:
    open_presence_session(user_id, after.status)

elif before.status != after.status:
    close_presence_session(user_id)
    open_presence_session(user_id, after.status)
```

Startup cleanup in `on_ready`: any `presence_sessions` rows with `ended_at IS NULL` are stale after a bot restart. `close_all_open_sessions()` closes them with `ended_at = NOW()` and computed `duration_seconds`. Load the new Cog in `main.py`:

```python
await bot.load_extension("src.cogs.presence")
```

#### EPIC-012 — Definition of Done

* [x] `Presence Intent` enabled in Discord Developer Portal (manual step — see deployment note)
* [x] `intents.presences = True` added to `main.py`
* [x] Migration SQL created and applied (`database/migration_003_presence_sessions.sql`)
* [x] `presence_service.py` implemented with open/close/startup-cleanup functions
* [x] `PresenceCog` added with `on_presence_update` listener
* [x] Startup cleanup runs on `cog_load` — no stale open sessions survive a bot restart
* [x] Going online, changing status, and going offline each produce correct rows in `presence_sessions`
* [x] `duration_seconds` is populated correctly when a session closes

---

### EPIC-013: Community Health Dashboard

* **Status:** Complete
* **Dependencies:** EPIC-011, EPIC-012, EPIC-004
* **Business Objective:** Give Community Managers a visual view of community growth and member presence patterns — complementing the engagement score already shown in EPIC-004.

#### EPIC-013 — Technical Scope

New service functions in `src/services/dashboard_service.py`:

```python
def get_member_events(days: int = 30) -> pd.DataFrame:
    """Rows from member_events for the last N days. Columns: user_id, event_type, created_at."""

def get_member_growth_summary(days: int = 30) -> pd.DataFrame:
    """Daily net growth (joins - leaves). Columns: date, joins, leaves, net."""

def get_presence_stats(days: int = 7) -> dict:
    """Avg session duration (seconds), total sessions, unique active members."""

def get_peak_hours(days: int = 7) -> pd.DataFrame:
    """Hourly online member count distribution. Columns: hour (0-23), avg_members."""
```

New "Community Health" tab in `src/dashboard/app.py`:

| Section | Content |
| --- | --- |
| Member Growth chart | Line chart — daily joins (green) vs leaves (red) vs net (blue), 30/60/90-day selector |
| Server size metric | Total members in `discord_users` today vs 30 days ago |
| Avg session duration | Mean `duration_seconds` over last 7 days, formatted as `Xh Ym` |
| Peak hours chart | Bar chart — average online members by hour of day (UTC) |
| Presence table | Top 10 members by total online time this week |

#### EPIC-013 — Definition of Done

* [x] All service functions added to `dashboard_service.py` (no Supabase calls inside `app.py`)
* [x] "Community Health" tab visible in the Streamlit app
* [x] Member Growth chart renders correctly with real data from `member_events`
* [x] Avg session duration and peak hours render correctly with data from `presence_sessions`
* [x] All sections show a clear empty-state message when data is absent
* [x] Existing dashboard tabs (Impact Pulse, The Lists, Admin) are unaffected (regression check)
