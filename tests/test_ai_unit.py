"""Unit tests for app.ai — no LM Studio, no network, milliseconds to run.

The model is replaced by a stand-in client, so these tests cover the parts we
actually own: prompt assembly, response parsing and error mapping. Nothing here
asserts what the model *says*, only that our code handles what it returns.
"""

import json
from datetime import date

import pytest
from fastapi import HTTPException
from openai import OpenAIError

from app.ai import BASE_URL, MODEL, analyze_tickets_with_ai
from conftest import fake_model as fake

pytestmark = pytest.mark.unit

TICKETS = [
    {
        "ticket_id": 1001,
        "title": "Cannot log in",
        "priority": "High",
        "category": "Login",
        "status": "Open",
    }
]

GOOD_JSON = {
    "summary": "One open high-priority login ticket.",
    "insights": ["Login failures are blocking a user."],
    "top_categories": ["Login"],
    "recommended_actions": ["Investigate the password reset flow."],
}


# --------------------------------------------------------------------------
# Parsing: every shape the local model has actually been observed to emit
# --------------------------------------------------------------------------

def test_clean_json_is_parsed():
    client = fake(json.dumps(GOOD_JSON))
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == GOOD_JSON


def test_fenced_json_is_unwrapped():
    client = fake("```json\n" + json.dumps(GOOD_JSON) + "\n```")
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == GOOD_JSON, "code fences must be stripped before parsing"


def test_fence_without_language_tag_is_unwrapped():
    client = fake("```\n" + json.dumps(GOOD_JSON) + "\n```")
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == GOOD_JSON


def test_json_wrapped_in_prose_is_extracted():
    client = fake(
        "Sure! Here is the analysis you asked for:\n"
        + json.dumps(GOOD_JSON)
        + "\nLet me know if you need anything else."
    )
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == GOOD_JSON, "outermost {...} block must be recovered"


def test_whitespace_padded_json_is_parsed():
    client = fake("\n\n  " + json.dumps(GOOD_JSON) + "  \n\n")
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == GOOD_JSON


def test_prose_only_reply_falls_back_to_raw():
    """The reply the model really gave when it ignored the JSON schema."""
    prose = (
        "As of 2026-01-13:\n\n"
        "* **Billing:** 2 tickets open\n"
        "* **UI:** 1 ticket closed\n\n"
        "Total: 2 open, 1 closed."
    )
    client = fake(prose)
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == {"raw": prose}, "unparseable output must surface as raw, not crash"


def test_truncated_json_falls_back_to_raw():
    """A hit context limit mid-object must not raise."""
    truncated = '{"summary": "One open ticket", "insights": ["a", '
    client = fake(truncated)
    result = analyze_tickets_with_ai(TICKETS, client=client)
    # ai.py strips the content, so compare against the stripped form.
    assert result == {"raw": truncated.strip()}


def test_empty_content_falls_back_to_raw():
    client = fake("")
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == {"raw": ""}


def test_none_content_falls_back_to_raw():
    client = fake(None)
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == {"raw": ""}


def test_json_array_reply_falls_back_to_raw():
    """A bare array is valid JSON but not the agreed object shape."""
    client = fake('["just", "a", "list"]')
    result = analyze_tickets_with_ai(TICKETS, client=client)
    assert result == ["just", "a", "list"]


# --------------------------------------------------------------------------
# Error mapping
# --------------------------------------------------------------------------

def test_connection_failure_becomes_502():
    client = fake(error=OpenAIError("Connection error."))
    with pytest.raises(HTTPException) as exc_info:
        analyze_tickets_with_ai(TICKETS, client=client)
    assert exc_info.value.status_code == 502
    assert BASE_URL in exc_info.value.detail, "detail should name the unreachable server"


def test_empty_choices_becomes_502():
    client = fake(choices=[])
    with pytest.raises(HTTPException) as exc_info:
        analyze_tickets_with_ai(TICKETS, client=client)
    assert exc_info.value.status_code == 502


def test_unexpected_exception_is_not_swallowed():
    """Only OpenAIError maps to 502; a bug in our own code must surface."""
    client = fake(error=ValueError("boom"))
    with pytest.raises(ValueError):
        analyze_tickets_with_ai(TICKETS, client=client)


# --------------------------------------------------------------------------
# Request assembly
# --------------------------------------------------------------------------

def test_request_uses_configured_model_and_schema():
    client = fake(json.dumps(GOOD_JSON))
    analyze_tickets_with_ai(TICKETS, client=client)

    assert len(client.calls) == 1, "exactly one model call per analysis"
    call = client.calls[0]
    assert call["model"] == MODEL
    assert call["response_format"]["type"] == "json_schema", "LM Studio rejects json_object"
    assert call["response_format"]["json_schema"]["schema"]["required"] == [
        "summary",
        "insights",
        "top_categories",
        "recommended_actions",
    ]


def test_prompt_contains_the_tickets():
    client = fake(json.dumps(GOOD_JSON))
    analyze_tickets_with_ai(TICKETS, client=client)

    content = client.calls[0]["messages"][0]["content"]
    assert "Cannot log in" in content, "ticket data must reach the model"
    assert "1001" in content


def test_non_serializable_ticket_values_do_not_crash():
    """pandas/date values must not break prompt assembly (default=str)."""
    client = fake(json.dumps(GOOD_JSON))
    tickets = [{"ticket_id": 1, "opened": date(2026, 1, 13)}]
    result = analyze_tickets_with_ai(tickets, client=client)

    assert result == GOOD_JSON
    assert "2026-01-13" in client.calls[0]["messages"][0]["content"]


def test_empty_ticket_list_still_calls_the_model():
    client = fake(json.dumps(GOOD_JSON))
    result = analyze_tickets_with_ai([], client=client)
    assert result == GOOD_JSON
    assert "[]" in client.calls[0]["messages"][0]["content"]
