import json

import google.generativeai as genai

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
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_SYSTEM_PROMPT,
    )
    response = model.generate_content(f"Analyze this text: {text}")
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
