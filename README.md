# Support Ticket Analyzer API

This project is a Support Ticket Analyzer built with FastAPI. It processes support tickets, allowing users to filter high priority tickets, open tickets, get categories, and generate reports in both JSON and CSV formats.

## Project Structure

- `app/` - Contains the main FastAPI application (`main.py`) and other core logic (`api.py`, `processor.py`, `utils.py`).
- `data/` - Directory for storing input ticket data.
- `output/` - Directory for generated JSON and CSV reports.

## Features

- **Get All Tickets (`GET /tickets`)**: Returns all support tickets.
- **Get Single Ticket (`GET /tickets/{ticket_id}`)**: Returns a specific ticket by ID.
- **Get High Priority Tickets (`GET /tickets/high`)**: Returns a list of high-priority tickets.
- **Get Open Tickets (`GET /tickets/open`)**: Returns a list of currently open tickets.
- **List Categories (`GET /categories`)**: Returns the available categories of the support tickets.
- **Analyze Tickets (`POST /analyze`)**: Accepts a list of tickets, normalizes them, and generates a summary report.
- **Filter Tickets (`POST /tickets/filter`)**: Filters tickets by priority, status, and category.
- **Generate JSON Report (`GET /report`)**: Summarizes all tickets and saves them into a JSON report.
- **Generate CSV Report (`GET /report/csv`)**: Prepares ticket data and saves it into a CSV report.

## Setup Instructions

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI application**:
   ```bash
   fastapi dev app/main.py
   # Or using uvicorn app.main:app --reload
   # Open: http://127.0.0.1:8000/docs
   ```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.
