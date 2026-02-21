# ADR-001: UNIFIED PYTHON STACK (Bot + Streamlit)

* **Date:** 2026-02-20
* **Status:** APPROVED

## 1. Context

We require a system comprising a persistent websocket-based bot and a web-based administrative dashboard. Historically, this might involve a Node.js/Python backend and a React/Vue frontend. However, the team size is small, and velocity is paramount.

## 2. Decision

We will use **Python 3.10+ for the entire stack**.

* **Backend/Bot:** `discord.py` (Asyncio).
* **Frontend/Dashboard:** `Streamlit`.
* **Shared Logic:** Pydantic V2 models sharing the `src/` directory.

## 3. Consequences (The "Why")

### Positive

* **Velocity:** No context switching between JavaScript and Python.
* **DRY (Don't Repeat Yourself):** Database models (Pydantic) and utility functions can be imported directly into the Dashboard without an API intermediary.
* **Hiring:** Simpler hiring profile (Python Generalist).

### Negative

* **Streamlit Limitations:** Streamlit is not designed for high-concurrency public usage. It re-runs the script on every interaction.
* **Mitigation:** The dashboard is internal-only. We will use `st.cache_data` aggressively for SQL queries.
* **UI Customization:** We are locked into Streamlit's widget set; custom CSS is brittle.

## 4. Rule Extraction (The "How" for Agents)

* **Target File:** `docs/architecture/rules/stack_rules.md`
* **Injected Constraint:**
    1. Do not introduce JavaScript frameworks (React/Vue/Next).
    2. All shared logic must reside in `src/core` or `src/models` to be importable by both `src/bot` and `src/dashboard`.
