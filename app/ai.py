# app/ai.py

import json
import os
from typing import Any

from fastapi import HTTPException
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

PROMPT = """You are a support operations analyst. Given the following support tickets (JSON),
produce a concise summary and actionable insights.

Return STRICT JSON with this shape:
{
  "summary": "<2-4 sentence overview of the tickets>",
  "insights": [
    "<short, specific insight #1>",
    "<short, specific insight #2>",
    "..."
  ],
  "top_categories": ["<category>", "..."],
  "recommended_actions": ["<action>", "..."]
}

Tickets:
"""


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set",
        )
    return genai.Client(api_key=api_key)


def analyze_tickets_with_ai(tickets: list[dict[str, Any]]) -> dict[str, Any]:
    client = _get_client()
    prompt = PROMPT + json.dumps(tickets, ensure_ascii=False)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}")

    text = (response.text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}
