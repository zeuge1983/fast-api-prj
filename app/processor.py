# app/processor.py


def summarize_tickets(tickets):
    summary = {
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

def prepare_tickets_for_csv(tickets):
    fields = ["title", "priority", "category", "status"]
    return [{field: ticket.get(field, "") for field in fields} for ticket in tickets]

def filter_high_priority(tickets):
    return [t for t in tickets if t["priority"] == "High"]

def filter_open_tickets(tickets):
    return [t for t in tickets if t["status"] == "Open"]

def get_categories(tickets):
    return list({t["category"] for t in tickets})