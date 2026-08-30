# Autonomous Communication & C2 Engine Backend

An enterprise-grade Python FastAPI backend for an Autonomous SMS Customer Service Gateway & Command Control (C2) Dashboard. The system processes incoming SMS webhooks, manages multi-turn conversation history using Redis, provides human-in-the-loop (HITL) agent handoffs, supports payment-bypass calendar booking overrides, enables live C2 management of knowledge base files (`/docs/*.md`), and integrates with Open WebUI and Docker Model Runner.

---

## Key Pillars & Architecture

1. **Payment-Bypass Calendar Booking Override (`calendar_service.py`)**:
   - Enables agents or automated triggers to schedule appointments directly into calendars bypassing invoice generation.
   - Sets status to `BOOKED_UNPAID_OVERRIDE` and generates instant Google Meet/calendar event invites sent via SMS.

2. **C2 Control Dashboard & File Engine (`c2_router.py`)**:
   - Provides live file management endpoints (`/api/c2/files`, `/api/c2/files/read`, `/api/c2/files/write`) allowing real-time editing of `/docs/*.md` knowledge base files without server restarts.
   - Provides C2 appointment override triggering (`/api/c2/calendar/override`).

3. **Open WebUI + Docker Model Runner & Containerization (`docker-compose.yml`)**:
   - Runs Open WebUI dashboard on port `3000`.
   - Orchestrates C2 backend, Redis session store, and Open WebUI services via Docker Compose.

4. **Multi-Turn Redis Memory & Telecom Gateway (`session_manager.py`, `main.py`)**:
   - Maintains windowed chat history (up to 10 messages) in Redis with automatic 2-hour inactivity TTL.
   - Supports TwiML XML (`application/xml`) or JSON responses.
   - Handles carrier opt-out keywords (`STOP`, `UNSUBSCRIBE`).

---

## Directory Structure

```text
.
├── docs/
│   ├── company_info.md
│   ├── faq.md
│   ├── sales/
│   │   └── pricing.md
│   ├── support/
│   │   └── help.md
│   └── vip/
│       └── concierge.md
├── calendar_service.py
├── c2_router.py
├── knowledge_base.py
├── personality_engine.py
├── session_manager.py
├── llm_service.py
├── main.py
├── test_app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Deployment & Setup

### 1. Run via Docker Compose
```bash
docker compose up -d --build
```
- Open WebUI Interface: `http://localhost:3000`
- FastAPI C2 Backend & API Docs: `http://localhost:8000/docs`

### 2. Run Locally (Development)
```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Running Unit Tests

Execute the full pytest suite:

```bash
pytest -v
```

---

## C2 Endpoint Reference

| Endpoint | Method | Description |
|---|---|---|
| `/webhook/sms` | `POST` | Inbound SMS Webhook (Form: `From`, `To`, `Body`). Returns JSON or TwiML XML. |
| `/agent/reply` | `POST` | Human Agent intervention reply to customer. |
| `/api/c2/files` | `GET` | List all `.md` knowledge base files in `/docs`. |
| `/api/c2/files/read` | `GET` | Read raw text content of a knowledge file. |
| `/api/c2/files/write` | `POST` | Create or update content of a `/docs/*.md` knowledge file. |
| `/api/c2/calendar/override` | `POST` | Trigger payment-bypass calendar booking override. |
