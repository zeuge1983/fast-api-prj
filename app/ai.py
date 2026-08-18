# app/ai.py

import json
import os
from typing import Any

from fastapi import HTTPException
from openai import OpenAI, OpenAIError

# Locally running Meta Muse Glimmer, served by LM Studio's OpenAI-compatible
# API. All three values can be overridden through the environment.
BASE_URL = os.environ.get("MUSE_BASE_URL", "http://localhost:1234/v1")
MODEL = os.environ.get("MUSE_MODEL", "meta/muse-glimmer")
API_KEY = os.environ.get("MUSE_API_KEY", "lm-studio")
TIMEOUT = float(os.environ.get("MUSE_TIMEOUT", "300"))

PROMPT = """You are a support operations analyst. Given the following support tickets (JSON),
produce a concise summary and actionable insights.

Reply with STRICT JSON only. No markdown, no code fences, no prose before or
after the JSON. Use exactly this shape:
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

# LM Studio only accepts response_format types "json_schema" or "text".
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "ticket_analysis",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "insights": {"type": "array", "items": {"type": "string"}},
                "top_categories": {"type": "array", "items": {"type": "string"}},
                "recommended_actions": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "summary",
                "insights",
                "top_categories",
                "recommended_actions",
            ],
            "additionalProperties": False,
        },
    },
}


def _get_client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=TIMEOUT)


def _parse_json(text: str) -> dict[str, Any]:
    """Best-effort JSON parse. Local models often wrap or pad their output."""

    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to the outermost {...} block if the model added prose around it.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return {"raw": text}


def analyze_tickets_with_ai(
    tickets: list[dict[str, Any]],
    client: OpenAI | None = None,
) -> dict[str, Any]:
    """Analyze tickets with the local model.

    `client` exists so tests can pass a stand-in and exercise this function
    without a running model. Production callers leave it as None.
    """

    client = client or _get_client()
    prompt = PROMPT + json.dumps(tickets, ensure_ascii=False, default=str)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format=RESPONSE_FORMAT,
        )
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Muse request to {BASE_URL} failed: {exc}",
        )

    if not response.choices:
        raise HTTPException(status_code=502, detail="Muse returned no choices")

    text = (response.choices[0].message.content or "").strip()

    return _parse_json(text)
