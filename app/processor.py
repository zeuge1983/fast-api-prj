# app/processor.py

from typing import Any


def summarize_tickets(tickets: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_tickets": len(tickets),
        "by_priority": {},
        "by_category": {}
    }

    for ticket in tickets:
        priority = ticket["priority"]
        category = ticket["category"]

        if priority not in summary["by_priority"]:
            summary["by_priority"][priority] = 0

        if category not in summary["by_category"]:
            summary["by_category"][category] = 0

        summary["by_priority"][priority] += 1
        summary["by_category"][category] += 1

    return summary

def prepare_tickets_for_csv(tickets: list[dict[str, Any]]) -> list:
    fields = ["title", "priority", "category", "status"]
    return [{field: ticket.get(field, "") for field in fields} for ticket in tickets]

def filter_high_priority(tickets: list[dict[str, Any]]) -> list:
    return [t for t in tickets if t["priority"] == "High"]

def filter_open_tickets(tickets: list[dict[str, Any]]) -> list:
    return [t for t in tickets if t["status"] == "Open"]

def get_categories(tickets: list[dict[str, Any]]) -> list:
    return list({t["category"] for t in tickets})

def normalize_tickets(ticket_models: list) -> list:
    return [t.model_dump() for t in ticket_models]

def filter_tickets(
        tickets: list[dict[str, Any]], 
        priority: str | None = None, 
        status: str | None = None, 
        category: str | None = None) -> list:
    result = tickets

    if priority:
        result = [t for t in result if t["priority"] == priority]

    if status:
        result = [t for t in result if t["status"] == status]

    if category:
        result = [t for t in result if t["category"] == category]

    return result

def get_ticket(tickets: list[dict[str, Any]], ticket_id: int) -> dict | None:
    ticket = next((t for t in tickets if t["ticket_id"] == ticket_id), None)

    return ticket
