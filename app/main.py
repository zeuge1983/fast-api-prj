# app/main.py

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.ai import analyze_tickets_with_ai
from app.auth import can_read_ticket, require_user
from app.api import load_tickets
from app.processor import filter_high_priority, summarize_tickets, prepare_tickets_for_csv, filter_open_tickets, get_categories, normalize_tickets, filter_tickets, get_ticket
from app.utils import save_report_json, save_report_csv
from app.models import TicketList, FilterRequest, TicketDetail

load_dotenv()

app = FastAPI()


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Report request validation failures as 400 Bad Request instead of 422."""
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors())},
    )

def get_tickets():
    return load_tickets()

@app.get("/tickets")
def get_all_tickets():
    
    tickets = get_tickets()

    return tickets

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

@app.post("/tickets/analyze-ai")
def analyze_tickets_ai(payload: TicketList | None = None):

    tickets = normalize_tickets(payload.tickets) if payload and payload.tickets else get_tickets()

    return analyze_tickets_with_ai(tickets)

@app.get("/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket_by_id(
    ticket_id: int = Path(gt=0, le=2147483647),
    user: dict = Depends(require_user),
):

    tickets = get_tickets()

    ticket = get_ticket(tickets, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not can_read_ticket(user, ticket):
        raise HTTPException(status_code=403, detail="Ticket belongs to another customer")

    return TicketDetail.from_row(ticket)

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