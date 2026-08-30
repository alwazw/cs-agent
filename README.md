# Autonomous Communication & C2 Engine Backend

An enterprise-grade Python FastAPI backend for an Autonomous SMS Customer Service Gateway, Telemetry Notification Center, and Command Control (C2) Dashboard. The system processes incoming SMS webhooks, manages multi-turn conversation history using Redis, provides human-in-the-loop (HITL) agent handoffs, supports payment-bypass calendar booking overrides, enables live C2 management of knowledge base files (`/docs/*.md`), tracks system telemetry alerts, and integrates with Open WebUI and Docker Model Runner.

---

## Key Pillars & System Architecture

1. **Payment-Bypass Calendar Booking Override (`calendar_service.py`)**:
   - Enables agents or automated triggers to schedule appointments directly into calendars bypassing invoice generation.
   - Sets status to `BOOKED_UNPAID_OVERRIDE` and generates instant Google Meet/calendar event invites sent via SMS.

2. **C2 Control Dashboard & File Engine (`c2_router.py`)**:
   - Live file management endpoints (`/api/c2/files`, `/api/c2/files/read`, `/api/c2/files/write`) allowing real-time editing of `/docs/*.md` knowledge base files without server restarts.
   - C2 appointment override triggering (`/api/c2/calendar/override`).

3. **Telemetry Monitor, Notification Center & Demo Simulation (`telemetry_service.py`)**:
   - Monitors token consumption velocity, stack health degradation, and latency.
   - Dispatches system alerts (`/api/c2/alerts`).
   - Built-in simulation endpoint (`/api/c2/demo/simulate?scenario=token_spike`) for testing sandbox notification alerts.

4. **Non-Conflicting Port Mapping & Docker Compose Containerization (`docker-compose.yml`)**:
   - Reconfigurable ports to avoid collisions with existing host services (e.g., existing Redis on 6379, existing Open WebUI on 3000, existing apps on 8000).
   - Defaults: `c2-backend` on port `9876:8000`, `open-webui-c2` on port `9875:8080`, `c2-redis` on port `9874:6379`.
   - Ports can be customized via environment variables (`C2_PORT`, `WEBUI_PORT`, `REDIS_HOST_PORT`).

---

## Directory Structure

```text
.
├── docs/
│   ├── USER_MANUAL.md
│   ├── company_info.md
│   ├── faq.md
│   ├── sales/
│   │   └── pricing.md
│   ├── support/
│   │   └── help.md
│   └── vip/
│       └── concierge.md
├── calendar_service.py
├── telemetry_service.py
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
- Open WebUI Interface: `http://localhost:9875` (configurable via `WEBUI_PORT`)
- FastAPI C2 Backend & API Docs: `http://localhost:9876/docs` (configurable via `C2_PORT`)

### 2. Custom Port Deployment Example
```bash
C2_PORT=9876 WEBUI_PORT=9875 REDIS_HOST_PORT=9874 docker compose up -d --build
```

### 3. Local Development Setup (Virtual Environment)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 9876
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
| `/api/c2/alerts` | `GET` | Retrieve real-time telemetry and token anomaly alerts. |
| `/api/c2/demo/simulate` | `POST` | Trigger simulated load tests (`token_spike`, `stack_failure`, `normal`). |
