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

* **Status:** Active
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
