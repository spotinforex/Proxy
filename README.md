# Proxy

> Your operations. Handled.

Proxy is an autonomous WhatsApp-based complaint resolution agent built for MCIPP running across Abia State, Nigeria. It replaces the manual work of a program operations coordinator: receiving complaints, looking up records, sending certificates, escalating to staff, and reporting to leadership — all without human intervention.

Built for the **Global AI Hackathon with Qwen Cloud** — Track 4: Autopilot Agent.

---

## The Problem

Every day, small business owners registered under MCIPP send WhatsApp messages asking the same questions:

- *"Where is my certificate?"*
- *"What is happening with my registration?"*
- *"Nobody has called me back."*

Behind those messages was a coordinator — a real person — manually checking spreadsheets, cross-referencing records, drafting responses, forwarding complaints to the right staff member, and compiling everything into a weekly report for leadership.

It worked. But it was slow, inconsistent, and dependent on one person being available.

We watched complaints pile up over weekends. We watched business owners wait days for answers that should have taken minutes. We watched the coordinator — who was us — spend hours every week on work that followed the same pattern every single time.

That pattern was the insight. **If the work is that predictable, an agent can do it.**

---

## What Proxy Does

A business owner sends a WhatsApp message. Proxy handles it end to end.

- **Registered business** — Proxy asks for their email and sends their certificate as an attachment. The owner receives their document within minutes, at any time of day.
- **Pending registration** — Proxy checks why it is pending. Missing documents? It tells them exactly what is needed. Processing delay? It gives a timeline.
- **Unresolvable complaint** — Proxy escalates to a staff member by email with full context already written up, so the human picking it up knows exactly what to do.
- **Leadership report** — A coordinator clicks a button on the dashboard. Proxy queries the database and generates a plain-English executive summary instantly.

Every complaint is logged. Every action is recorded. Every resolution is tracked.

---

## Agent Architecture

Proxy runs a four-agent pipeline powered by Qwen on Qwen Cloud.

```
WhatsApp message
      ↓
FastAPI pipeline — debounce, merge, conversation state
      ↓
Triage Agent — classifies intent, extracts owner name and business
      ↓ (if info missing → ask user, wait for reply)
Supabase — create complaint record, look up business
      ↓
Registration Agent — checks status, decides action, writes response
      ↓
   ┌──────────────┬──────────────┬──────────────┐
AWAIT_EMAIL   AWAIT_DOCS     RESOLVED       ESCALATE
send cert     list missing   close record   email staff
      ↓
Supabase — log every action, update complaint status

Dashboard request (separate flow)
      ↓
Report Agent — queries Supabase, drafts executive summary
      ↓
Report rendered on dashboard
```

**Triage Agent** — Reads every incoming message and figures out what the user wants. Extracts the business name, owner name, and intent. If information is missing, it asks for it naturally before routing forward.

**Registration Agent** — Receives the classified complaint and the business record. Follows a decision tree and uses Qwen to write every response itself. No hardcoded templates. Every WhatsApp reply, email subject, and email body is drafted by the agent. When a complaint cannot be resolved, it compiles full context and notifies staff by email.

**Report Agent** — Triggered from the dashboard on demand. Queries the database for complaint volumes, resolution rates, and open issues. Generates a plain-English summary for program leadership.

---

## Stack

| Layer | Technology |
|---|---|
| Agent reasoning | Qwen (via Qwen Cloud / DashScope) |
| WhatsApp | Green API |
| Backend | FastAPI |
| Database | PostgreSQL on Supabase |
| Email | SMTP (Gmail or any provider) |
| Cloud | Alibaba Cloud |

---

## Architectural Diagram

![System Architecture](images/proxy_agent_orchestration_v3.png)

---

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) — fast Python package manager
- A Qwen Cloud account with API access
- A Green API instance connected to a WhatsApp number
- A Supabase project with the schema below
- An SMTP account for email delivery (Gmail works)

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone and install

```bash
git clone https://github.com/spotinforex/proxy.git
cd proxy
uv sync
```

### Environment variables

Create a `.env` file in the project root:

```env
# Qwen Cloud
DASHSCOPE_API_KEY=your_dashscope_api_key

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Green API (WhatsApp)
GREEN_API_INSTANCE_ID=your_instance_id
GREEN_API_TOKEN=your_token

# Webhook security
WEBHOOK_TOKEN=your_secret_token

# Email
smtp-host=smtp.gmail.com
smtp-port=587
smtp-user=your@gmail.com
smtp-pass=your_app_password
CC_RECIPIENT=cc@example.com
SENDER_NAME=MCIPP Support

# Staff
STAFF_EMAIL=staff@mcipp.org
```

> Never commit `.env` to version control.

### Run the server

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/webhook` | Receives incoming Green API webhook payloads. Requires `Authorization: Bearer <WEBHOOK_TOKEN>` |
| GET | `/ws` | WebSocket for live dashboard updates |
| GET | `/api/pipeline/report` | Triggers the Report Agent and returns the generated summary |
| GET | `/api/pipeline/complaints` | Returns all complaints for the dashboard |
| GET | `/api/pipeline/export` | Downloads complaints as Excel |

---

## How the Pipeline Handles a Conversation

People do not send one clean message. They send three. Proxy handles this through conversation memory and debouncing.

When multiple messages arrive in quick succession from the same number, they are buffered and merged before hitting the pipeline. The full conversation history is passed into every agent call so Proxy remembers what was already said without asking the user to repeat themselves.

Conversation state tracks where each phone number is in the resolution flow — waiting for an email address, waiting for documents, or fully resolved. This state persists across messages until the complaint is closed.

---

## Troubleshooting

**Webhook returns 401** — Check that `WEBHOOK_TOKEN` in `.env` matches the token the client sends as `Authorization: Bearer <token>`.

**Agent returns malformed JSON** — Check `DASHSCOPE_API_KEY` is set correctly. Raw model output is logged on parse failures.

**Certificate not attaching** — Ensure `certificate_url` in the `businesses` table is a valid HTTPS URL, not a local path or backslash-separated string. The email handler fetches attachments from URLs at send time.

**Email going to spam** — Ensure `SENDER_NAME` is set. The handler adds proper `From`, `Date`, and `Message-ID` headers automatically. Consider setting up SPF/DKIM on your sending domain for production.

---

## Links
**Youtube Video Link**: [Proxy Video](https://youtu.be/UCj4wtsZkUU)

**Blog Post Link**: [Proxy Blog](https://medium.com/@nwabekepraisejah/we-built-an-ai-agent-to-do-our-job-here-is-what-happened-1c2bd01867eb)

**Dashboard Link**:[Proxy App](http://47.236.152.221:3000)

---

## License

Apache