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
- **AI Analyze Tickets (`POST /tickets/analyze-ai`)**: Sends tickets to a locally running Meta Muse Glimmer model (served by [LM Studio](https://lmstudio.ai/) on its OpenAI-compatible API) and returns a summary plus insights. Sends loaded tickets by default; pass `{ "tickets": [...] }` in the body to analyze a custom list. Requires LM Studio running with the model loaded. Configurable via `MUSE_BASE_URL` (default `http://localhost:1234/v1`), `MUSE_MODEL` (default `meta/muse-glimmer`), `MUSE_API_KEY` (default `lm-studio`) and `MUSE_TIMEOUT` seconds (default `300`).

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
   ```
   Or using
   ```bash
   uvicorn app.main:app --reload
   http://127.0.0.1:8000/docs
   ```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Docker

### Prerequisites

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your platform (Mac, Windows, or Linux).

### Dockerfile

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .dockerignore

```
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.env
output/
```

### Docker Compose (recommended)

A `docker-compose.yml` is provided. It reads `.env` automatically, so you don't need any `-e` flags.

```bash
docker compose up --build      # build and start
docker compose up -d           # start in the background
docker compose logs -f         # follow logs
docker compose down            # stop and remove
```

### Build and Run manually

1. **Build the image**:
   ```bash
   docker build -t ticket-api .
   ```

2. **Run the container** (pass your Gemini API key for the AI endpoint):
   ```bash
   docker run -p 8000:8000 --env-file .env ticket-api
   ```

The API will be available at `http://localhost:8000`. Access the interactive API documentation (Swagger UI) at `http://localhost:8000/docs`.
