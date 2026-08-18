"""Grounding checks: is every claim in the analysis traceable to the input?

These are plain functions, not tests, for two reasons: tests can call them
against any model output, and the functions themselves can be tested (a
detector nobody has verified is not evidence of anything).

A number is considered grounded if it either appears somewhere in the supplied
ticket data, or is a count you could legitimately derive from it.
"""

import json
import re
from collections import Counter


def _grounded_numbers(tickets):
    """Every integer a truthful summary could cite."""

    allowed = set()

    # Numbers present anywhere in the input (ids, "error 502", "3 weeks"...).
    for token in re.findall(r"\d+", json.dumps(tickets, default=str)):
        allowed.add(int(token))

    if not tickets:
        return allowed | {0}

    # Aggregate counts a summary is entitled to compute.
    allowed.add(len(tickets))
    for field in ("status", "priority", "category", "customer_name"):
        counts = Counter(t[field] for t in tickets if field in t)
        allowed.update(counts.values())

    return allowed


def ungrounded_numbers(analysis, tickets):
    """Integers the summary cites that the input cannot justify."""

    summary = analysis.get("summary", "")
    claimed = {int(n) for n in re.findall(r"\b(\d+)\b", summary)}

    return claimed - _grounded_numbers(tickets)


def invented_categories(analysis, tickets):
    """Categories the analysis names that were never in the input."""

    real = {t["category"] for t in tickets if "category" in t}

    return set(analysis.get("top_categories", [])) - real
