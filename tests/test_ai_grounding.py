"""Do the grounding checks actually catch a real hallucination?

Every reply used here is a real one, recorded from the local model in
tests/cassettes/. The point of this module is not to test the model — it is to
test the DETECTOR, using one reply known to be accurate and one known to be
wrong.
"""

import pytest

from app.ai import analyze_tickets_with_ai
from app.api import load_tickets
from tests.grounding import invented_categories, ungrounded_numbers

pytestmark = pytest.mark.unit

TWO_TICKETS = [
    {
        "ticket_id": 1,
        "title": "Refund not received",
        "priority": "High",
        "category": "Billing",
        "status": "Open",
        "description": "Customer waiting 3 weeks for refund.",
    },
    {
        "ticket_id": 2,
        "title": "Dark mode request",
        "priority": "Low",
        "category": "Feature Request",
        "status": "Open",
        "description": "Wants dark theme.",
    },
]


# --- positive control: an accurate reply must pass -------------------------

def test_accurate_reply_is_grounded(cassette):
    analysis = analyze_tickets_with_ai(TWO_TICKETS, client=cassette("two-tickets"))

    assert ungrounded_numbers(analysis, TWO_TICKETS) == set()
    assert invented_categories(analysis, TWO_TICKETS) == set()


# --- negative control: the known-bad reply must be caught -----------------

def test_hallucinated_count_is_caught(cassette):
    """The real reply claimed 11 tickets when 12 were supplied."""

    tickets = load_tickets()
    analysis = analyze_tickets_with_ai(tickets, client=cassette("full-ticket-set"))

    assert len(tickets) == 12, "cassette was recorded against 12 tickets"
    assert ungrounded_numbers(analysis, tickets) == {11}, (
        "the detector must flag 11 as ungrounded, and flag nothing else — "
        "every other figure in that reply was correct"
    )


def test_categories_in_the_bad_reply_were_still_real(cassette):
    """Shows the checks are independent: this reply hallucinated a count,
    but did not invent any category."""

    tickets = load_tickets()
    analysis = analyze_tickets_with_ai(tickets, client=cassette("full-ticket-set"))

    assert invented_categories(analysis, tickets) == set()


# --- the check that would run against live output --------------------------

def test_invented_category_would_be_caught():
    """Hand-built output, to prove the category check can fail at all."""

    analysis = {"summary": "All quiet.", "top_categories": ["Cryptocurrency"]}

    assert invented_categories(analysis, TWO_TICKETS) == {"Cryptocurrency"}
