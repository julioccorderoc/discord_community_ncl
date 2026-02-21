# Known Errors & Gotchas

A log of bugs, footguns, and non-obvious failures encountered during development.
Check this before debugging — the answer may already be here.

---

## Gemini SDK — Package Deprecated

**Symptom:** `FutureWarning: All support for the google.generativeai package has ended.`
**Cause:** `google-generativeai` is fully deprecated as of Nov 2025.
**Fix:** Use `google-genai` instead. Import as `from google import genai`.
**Status:** Resolved — `google-genai` is the installed package.

---

## Gemini API — Model Not Found (404)

**Symptom:** `ClientError: 404 NOT_FOUND — models/gemini-X is not found for API version v1beta`
**Cause:** The new `google-genai` SDK targets the `v1beta` endpoint. Not all model names are available there, and availability varies by API key account type.

Known broken model IDs (for new API accounts):

- `gemini-1.5-flash` — only served on the `v1` path, not `v1beta`
- `gemini-2.0-flash` — "no longer available to new users"

**Fix:** Use `gemini-2.0-flash-lite` as the default. Model is configurable via `GEMINI_MODEL` in `.env` so it can be changed without a code deploy.
**Status:** Resolved — `GEMINI_MODEL` defaults to `gemini-2.0-flash-lite` in `src/config.py`.

---

## Discord — Slash Command Interaction Stuck on "Thinking..."

**Symptom:** Bot shows "thinking..." in Discord indefinitely after a slash command is invoked. No response ever appears. The error is visible in bot logs but not in Discord.
**Cause:** An unhandled exception inside the slash command handler causes `discord.py` to log and exit the handler without ever calling `interaction.followup.send()`. Discord's deferred interaction has no response and hangs.
**Fix:** Always wrap the body of every slash command handler in `try/except Exception` and call `interaction.followup.send(...)` in the except block.
**Status:** Resolved — `src/cogs/audit.py` and `src/cogs/tickets.py` both follow this pattern.

---

## Gemini — `genai.Client` Created Per Call (Performance)

**Symptom:** Unnecessary overhead on every `/audit` invocation.
**Cause:** `genai.Client(api_key=...)` was originally instantiated inside `analyze_text()`, meaning a new HTTP client and auth context was built on every call.
**Fix:** Move client instantiation to module level as a singleton (`_client = genai.Client(...)`). Import time is acceptable; per-call is not.
**Status:** Resolved — `src/services/ai_service.py` initialises `_client` at import time.
