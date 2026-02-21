# PRODUCT REQUIREMENTS DOCUMENT: COMMUNITY OS

* **Version:** 1.0.0
* **Last Updated:** 2026-02-20
* **Primary Human Owner:** Technical Product Manager

## 1. Core Objective

To replace ad-hoc Discord community management with a centralized, data-driven "Operating System." The system will unify engagement tracking, support ticketing, and AI-assisted compliance into a single Python monorepo, providing internal stakeholders with a dashboard to visualize community health and operationalize support.

## 2. Strict Scope Boundaries

### In-Scope (Must Have)

* **Engagement Telemetry:** Ingestion of Discord events (Messages, Reactions) to calculate a weighted "Community Score" per user. Formula: `Score = (Messages × 1) + (Reactions × 0.5)`.
* **Support Ticketing:** A dedicated channel-based ticket system with database-backed state management (`Open` -> `In Progress` -> `Resolved`).
* **Unified Dashboard:** A Streamlit interface for Creator Managers to view "Rising Stars" (High Engagement) and track tickets (simple, to overview the numbers).
* **AI Compliance Layer:** On-demand `/audit` command using LLMs to flag toxic/unsafe content, with strict cost accounting per request.
* **Identity Resolution:** 1:1 mapping of Discord IDs to Supabase User Profiles.

### Out-of-Scope (Anti-Goals - CRITICAL FOR AI)

* **Payment Processing:** No handling of subscriptions or fiat transactions.
* **Moderation Automation:** No auto-banning or auto-kicking logic (Human-in-the-loop only).
* **Public-Facing Web App:** The dashboard is for *internal staff only*.
* **Complex ORM Layers:** No SQLAlchemy or Tortoise ORM usage allowed.
* **Voice Tracking (MVP):** Voice event tracking is deferred to post-MVP. No voice duration recording in the current scope.
* **Voice Transcription:** We will never record or transcribe audio content.
* **Auth:** No authentication or authorization, this solution is too have data transparency and assumes only team member have access to it

## 3. User Personas

* **The Creator Manager (Sole User):**
  * **Primary Goal:** "I need to know if the event I ran yesterday actually increased engagement, or if it was a waste of time."
  * **Secondary Goal:** "I need a 'Kill List' of users likely to churn so I can DM them, and a 'VIP List' of rising stars to promote."
  * **Constraint:** Zero tolerance for complex SQL queries; needs visual answers immediately.
* **System Administrator (The Developer):**
  * **Role:** The technical partner building and maintaining the OS for the Creator.
  * **Primary Goal:** "I need to ensure the bot is online and the database is healthy without SSH-ing into a server."
  * **Secondary Goal:** "I need to track AI token usage (Anthropic/Gemini) to accurately bill the client or set hard limits."
  * **Critical Need:** Observability. If the bot crashes or an API fails, I need to know *why* immediately via a log stream in the Admin Dashboard, not just a console error.

## 4. Dashboard specific requirements (Impact & Insight)

* **Cohort Tracking:** Ability to tag a timeframe (e.g., "Summer Campaign") and see engagement lift relative to baseline.
* **Churn Radar:** List of users whose engagement dropped >50% week-over-week.
* **Star Scouter:** List of users who joined <30 days ago but are in the top 10% of activity.
* **Admin Mode**
  * **Toggle:** A specific view only visible to the Developer (via a simple password).
  * **Health Check:** Green/Red status for Discord Gateway, Supabase Connection, and OpenAI API.
  * **Cost Ledger:** A running total of AI costs for the current billing cycle (to prevent eating into the project margin).
  * **Panic Button:** A "Stop Bot" or "Flush Cache" button to reset state without redeploying code.

## 5. Success Criteria (Definition of Done)

1. **Latency:** Dashboard loads key metrics (Top 10 Users) in < 2.0 seconds.
2. **Data Integrity:** 100% of Ticket State changes are logged to Supabase with timestamps.
3. **Reliability:** The Bot auto-reconnects after downtime; Streamlit dashboard persists connection to DB.
4. **Security:** No raw SQL strings containing user input (100% Parameterized).
