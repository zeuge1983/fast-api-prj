# Support Ticket Analyzer API

This project is a Support Ticket Analyzer built with FastAPI. It processes support tickets, allowing users to filter high priority tickets, open tickets, get categories, and generate reports in both JSON and CSV formats.

## Project Structure

- `app/` - Contains the main FastAPI application (`main.py`) and other core logic (`api.py`, `processor.py`, `utils.py`).
- `data/` - Directory for storing input ticket data.
- `output/` - Directory for generated JSON and CSV reports.

## Features

- **Home Endpoint (`/`)**: API health check.
- **Generate JSON Report (`/report`)**: Summarizes tickets and saves them into a JSON report.
- **High Priority Tickets (`/tickets/high`)**: Returns a list of high-priority tickets.
- **Open Tickets (`/tickets/open`)**: Returns a list of currently open tickets.
- **Categories (`/categories`)**: Returns the available categories of the support tickets.
- **Generate CSV Report (`/report/csv`)**: Prepares ticket data and saves it into a CSV report.

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
