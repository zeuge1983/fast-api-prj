# app/main.py

from fastapi import FastAPI
from app.api import load_tickets
from app.processor import filter_high_priority, summarize_tickets, prepare_tickets_for_csv, filter_open_tickets, get_categories, normalize_tickets, filter_tickets
from app.utils import save_report_json, save_report_csv
from app.models import TicketList, FilterRequest

app = FastAPI()

def get_tickets():
    return load_tickets()

@app.get("/")
def home():
    return {"message": "Support Ticket Analyzer API"}

@app.get("/report")
def generate_json_report():

    report = summarize_tickets(get_tickets())

    save_report_json(report)

    return report

@app.get("/tickets/high")
def get_high_priority_tickets():

    high_priority_tickets = filter_high_priority(get_tickets())

    return high_priority_tickets

@app.get("/tickets/open")
def get_open_tickets():

    open_tickets = filter_open_tickets(get_tickets())

    return open_tickets

@app.get("/categories")
def list_categories():

    categories = get_categories(get_tickets())

    return categories

@app.get("/report/csv")
def generate_csv_report():

    csv_data = prepare_tickets_for_csv(get_tickets())

    save_report_csv(csv_data)

    return {"message": "CSV report saved", "total_tickets": len(csv_data)}

@app.post("/analyze")
def analyze_tickets(payload: TicketList):

    tickets = normalize_tickets(payload.tickets)

    report = summarize_tickets(tickets)

    save_report_json(report)

    return report

@app.post("/tickets/filter")
def filter_endpoint(payload: FilterRequest):
    tickets = normalize_tickets(payload.tickets)

    filtered = filter_tickets(
        tickets,
        priority=payload.priority,
        status=payload.status,
        category=payload.category
    )

    return {
        "total": len(filtered),
        "tickets": filtered
    }