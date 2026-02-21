import json
import logging
import time

from google import genai
from google.genai import types

import src.config as config

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a compliance agent for an online creator community. "
    "Analyze the provided text for potential policy violations, toxic behavior, "
    "harassment, spam, or other community guideline risks. "
    'Respond ONLY with valid JSON in this exact format: '
    '{"rating": "green" | "yellow" | "red", "summary": "<2-3 sentence assessment>"} '
    "- green: no issues detected "
    "- yellow: monitor — borderline or minor concerns "
    "- red: action needed — clear violation or serious risk"
)

# Client is created once at import time — not on every call.
_client = genai.Client(api_key=config.GEMINI_API_KEY)


def analyze_text(text: str) -> dict:
    """Call Gemini and return analysis result with telemetry fields.

    Returns a dict with keys:
      rating, summary          — parsed LLM output
      raw_response             — verbatim LLM text (for audit logging)
      tokens_used              — total token count from usage_metadata
      elapsed_ms               — wall-clock round-trip in milliseconds

    Falls back to rating='unknown' if JSON parsing fails.
    """
    log.info("[audit] Sending request to Gemini (text length: %d chars)", len(text))
    t0 = time.perf_counter()

    response = _client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=f"Analyze this text: {text}",
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
        ),
    )

    elapsed = time.perf_counter() - t0
    elapsed_ms = int(elapsed * 1000)
    log.info("[audit] Gemini responded in %.2fs", elapsed)

    raw = response.text.strip()
    log.debug("[audit] Raw response: %s", raw)

    tokens_used: int | None = None
    if response.usage_metadata:
        tokens_used = response.usage_metadata.total_token_count

    # Strip markdown code fences if the model wraps the JSON.
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        log.info("[audit] Parsed result — rating: %s", result.get("rating"))
        return {
            "rating": result.get("rating", "unknown"),
            "summary": result.get("summary", ""),
            "raw_response": raw,
            "tokens_used": tokens_used,
            "elapsed_ms": elapsed_ms,
        }
    except json.JSONDecodeError:
        log.warning("[audit] JSON parse failed — returning raw response as summary")
        return {
            "rating": "unknown",
            "summary": raw,
            "raw_response": raw,
            "tokens_used": tokens_used,
            "elapsed_ms": elapsed_ms,
        }


def log_ai_audit(
    user_id: int,
    command_name: str,
    input_prompt: str,
    llm_response: str | None,
    tokens_used: int | None,
    processing_time_ms: int | None,
) -> None:
    """Write one row to ai_audit_logs. Swallows exceptions to never block the bot."""
    from src.database.client import supabase  # local import avoids circular dependency at module load
    try:
        supabase.table("ai_audit_logs").insert({
            "user_id": user_id,
            "command_name": command_name,
            "input_prompt": input_prompt,
            "llm_response": llm_response,
            "tokens_used": tokens_used,
            "processing_time_ms": processing_time_ms,
        }).execute()
        log.info("[audit] ai_audit_log written for user_id=%s", user_id)
    except Exception:
        log.exception("[audit] Failed to write ai_audit_log — continuing without logging")


def check_gemini_health() -> bool:
    """Return True if the Gemini API is reachable, False otherwise."""
    try:
        _client.models.list()
        return True
    except Exception:
        log.warning("[health] Gemini health check failed")
        return False
