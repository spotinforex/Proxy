# Proxy — Backend README

## Overview

This repository contains the backend for the Proxy service — an autonomous complaint resolution system used by MCIPP to triage, log and resolve complaints coming from WhatsApp/webhooks and to run agents that analyze and generate management reports.

The backend is a FastAPI application (see `main.py`) and includes pipeline logic, agents, database utilities and helper tools.

## Features

- Webhook receiver for incoming messages (`/webhook`)
- WebSocket endpoint for live updates (`/ws`)
- Complaint processing pipeline with triage and registration agents
- Email sending utilities
- Management report agent that generates JSON-structured executive reports

## Requirements

- Python 3.10+ (tested with 3.11)
- Dependencies listed in `pyproject.toml` (or install via pip)

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # or `pip install .` if using pyproject
```

## Environment variables

Create a `.env` file in the project root (this repository already contains a `.env` example). Important variables used by the backend include:

- `WEBHOOK_TOKEN` — secret token required by the webhook handler (used by the frontend/API client as `Authorization: Bearer <token>`)
- `DASHSCOPE_API_KEY` — API key used by the report agent (OpenAI/Dashscope client)
- `DATABASE_URL` — Postgres connection URL for persistence
- `smtp-host`, `smtp-port`, `smtp-user`, `smtp-pass` — SMTP configuration for sending emails
- `GREEN_API_INSTANCE_ID`, `GREEN_API_TOKEN` — integration tokens (if used)
- `STAFF_EMAIL`, `SENDER_NAME` — email sender and recipient defaults

Security note: Keep these values secret. Do not commit `.env` with secrets to version control.

## Running the app (development)

Start the FastAPI server locally (example using `uvicorn`):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server exposes the following endpoints (see "API" below).

## API Endpoints

- `POST /webhook` — receives incoming webhook payloads. Requires bearer token authorization matching `WEBHOOK_TOKEN`.
- `GET /ws` — websocket endpoint for subscribing to live updates from the backend pipeline.

Additionally, the frontend uses API routes under `/api/pipeline/*` which proxy to pipeline functions (check `pipeline` package and frontend `pipelineAPI` client in `frontend/src/api/client.js`).

## Pipeline & Agents

- The pipeline flow is implemented in `pipeline/process.py` and handles message debouncing, triage, creating complaint records, running the registration agent, and taking follow-up actions (send messages, escalate, email certificates).
- The report agent (`agents/report_agent.py`) generates structured JSON reports using the system prompt in `agents/system_prompt/report_system_prompt.txt`.

## Development notes

- The frontend client sets `Authorization: Bearer <token>` on requests; ensure `WEBHOOK_TOKEN` matches the client if running locally without authentication changes.
- The code includes session memory and de-duplication utilities to avoid processing duplicate messages.
- When modifying agents or prompts, keep the report agent's expected JSON return format in `agents/system_prompt/report_system_prompt.txt`.

## Tests

Run unit tests in the `tests/` directory with pytest:

```bash
pytest -q
```

## Troubleshooting

- Invalid token errors: verify `.env` has `WEBHOOK_TOKEN` set and the client sends the bearer token correctly.
- Report agent returns null: ensure `DASHSCOPE_API_KEY` is configured and the agent returns valid JSON; logs will show raw model output on JSON parse failures.

## Contact

For questions about the backend implementation or deployment, reach out to the project maintainer.
