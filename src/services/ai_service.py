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
    """Call Gemini and return a dict with 'rating' and 'summary' keys.

    Falls back to {'rating': 'unknown', 'summary': <raw response>} if JSON
    parsing fails.
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
    log.info("[audit] Gemini responded in %.2fs", elapsed)

    raw = response.text.strip()
    log.debug("[audit] Raw response: %s", raw)

    # Strip markdown code fences if the model wraps the JSON.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
        log.info("[audit] Parsed result — rating: %s", result.get("rating"))
        return result
    except json.JSONDecodeError:
        log.warning("[audit] JSON parse failed — returning raw response as summary")
        return {"rating": "unknown", "summary": raw}
