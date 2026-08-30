# SMS Customer Service Chatbot Backend

A production-ready Python FastAPI backend for an SMS customer service chatbot. The system processes incoming SMS webhooks, manages multi-turn conversation history using Redis, dynamically assigns initiative knowledge bases and personalities by destination phone number (`To`), provides human-in-the-loop (HITL) agent handoff, handles carrier opt-out keywords (STOP/UNSUBSCRIBE), and generates async LLM responses via standard `openai` SDK or local OpenAI-compatible inference servers (LM Studio, Ollama).

---

## Key Features

- **FastAPI Webhook**: `POST /webhook/sms` endpoint processing form payloads (`From`, `To`, `Body`). Supports both JSON and TwiML XML (`application/xml`) output formats.
- **Flexible LLM Endpoints**: Configurable for OpenAI API or local inference servers (LM Studio, Ollama) via `LOCAL_LLM_URL` and `LLM_MODEL`.
- **Session History & Memory (Redis / Async)**: Persists up to 10 messages (last 5 user/assistant turns) per customer in Redis using async pipeline calls with automatic 2-hour inactivity expiration (TTL). Includes a zero-config in-memory fallback when Redis is offline.
- **Async LLM Integration**: Uses `AsyncOpenAI` for non-blocking LLM completions incorporating windowed chat history, persona instructions, and local Markdown documentation.
- **Human-in-the-Loop (HITL) Handoff**: Detects escalation keywords (`agent`, `human`, `representative`, `operator`), shifts state to `HUMAN_REQUESTED`, and provides a `POST /agent/reply` endpoint for human support agents to reply directly.
- **Carrier Opt-Out (STOP / UNSUBSCRIBE)**: Complies with SMS carrier requirements by flagging opted-out numbers and halting LLM execution until resubscribed (`START`).
- **Initiative & Phone Mapping**: Dynamically routes requests based on recipient phone number (`To`) to dedicated `/docs` subdirectories (e.g. `/docs/support`, `/docs/sales`) and persona configurations.
- **Comprehensive Unit Testing**: Pytest suite using `TestClient` and `anyio` testing session storage, HITL escalation, TwiML output, opt-out handling, and async LLM execution.

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
├── knowledge_base.py
├── personality_engine.py
├── session_manager.py
├── llm_service.py
├── main.py
├── test_app.py
├── requirements.txt
└── README.md
```

---

## Setup & Configuration

### 1. Prerequisites
- Python 3.10+
- Redis (Optional; automatically falls back to in-memory store if Redis is unavailable)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
- **Cloud OpenAI Configuration**:
  ```bash
  export OPENAI_API_KEY="your-openai-api-key"
  export LLM_MODEL="gpt-4o-mini"
  ```

- **Local Inference Server Configuration (LM Studio / Ollama)**:
  ```bash
  export LOCAL_LLM_URL="http://localhost:1234/v1"  # LM Studio default
  # export LOCAL_LLM_URL="http://localhost:11434/v1" # Ollama default
  export LLM_MODEL="qwen2.5-3b-instruct"
  ```

- **Redis Configuration**:
  ```bash
  export REDIS_HOST="localhost"   # Optional (default: localhost)
  export REDIS_PORT=6379          # Optional (default: 6379)
  ```

---

## Telecom Architecture & Economic Scaling Guide

| Scale Phase | Infrastructure Strategy | Telecom Provider | Estimated Segments/Day | Approx. Telecom Bill |
|---|---|---|---|---|
| **Phase 1: Dev & Testing** | Android + Tasker/TextBee + Local LM Studio | Free / Local | < 100 | $0 / mo |
| **Phase 2: Growth** | FastAPI + Local 10DLC Numbers | Telnyx / SignalWire | 1,000 – 5,000 | ~$150 – $750 / mo |
| **Phase 3: High Scale** | FastAPI + Dedicated Short Code (100+ MPS) | Enterprise Telnyx | 100,000+ | Wholesale per-segment rates |

---

## Running the Application

Start the FastAPI backend with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation is available at `http://localhost:8000/docs`.

---

## Testing

Execute the complete test suite:

```bash
pytest -v
```

---

## Usage Examples

### 1. Standard SMS Webhook Request (JSON Output)
```bash
curl -X POST "http://localhost:8000/webhook/sms" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+15551234567&To=+18005550100&Body=How%20do%20I%20return%20an%20item%3F"
```

### 2. Twilio TwiML XML Response
```bash
curl -X POST "http://localhost:8000/webhook/sms" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+15551234567&To=+18005550100&Body=Hello"
```

### 3. Human Agent Reply Endpoint
```bash
curl -X POST "http://localhost:8000/agent/reply" \
  -H "Content-Type: application/json" \
  -d '{"customer_number": "+15551234567", "message": "Hi, I am Agent Smith. How can I assist you?"}'
```
