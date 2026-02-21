import json

from google import genai
from google.genai import types

import src.config as config

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


def analyze_text(text: str) -> dict:
    """Call Gemini and return a dict with 'rating' and 'summary' keys.

    Falls back to {'rating': 'unknown', 'summary': <raw response>} if JSON
    parsing fails.
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=f"Analyze this text: {text}",
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
        ),
    )
    raw = response.text.strip()

    # Strip markdown code fences if the model wraps the JSON.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"rating": "unknown", "summary": raw}
