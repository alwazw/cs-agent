# SMS Customer Service Chatbot Backend

A Python FastAPI backend for an SMS customer service chatbot. The system processes incoming SMS webhooks, loads local Markdown documentation as a knowledge base, dynamically assigns personalities or initiative mappings by destination phone number (`To`), and generates an LLM response using standard OpenAI SDK.

---

## Features

- **FastAPI Webhook**: Serves a `POST /webhook/sms` endpoint accepting form payloads (`From`, `To`, `Body`).
- **Initiative & Phone Mapping**: Dynamically identifies the target initiative (knowledge base subfolder and personality persona) based on the recipient phone number (`To`).
- **Knowledge Base Loader**: Scans local `/docs` (and initiative subdirectories like `/docs/support`) on startup and aggregates `.md` files into LLM context.
- **Personality Engine**: Configured with 3 distinct conversational personas ("Warm and Empathetic", "Crisp and Professional", "Witty and Casual") assigned via initiative mapping or random selection per request.
- **LLM Integration**: Uses standard `openai` SDK to generate concise SMS-suitable responses combining system prompt, knowledge base context, and user input.
- **Comprehensive Testing**: Pytest unit tests using FastAPI `TestClient` covering file loading, phone number mapping, personality engine, and mocked LLM webhook responses.

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
├── llm_service.py
├── main.py
├── test_app.py
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10+

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Set your OpenAI API Key:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

---

## Running the Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be accessible at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

---

## Testing

Run the test suite using `pytest`:

```bash
pytest -v
```

---

## Example Usage

### 1. Standard Request (Mapped Phone Number)
Send an SMS to the Support initiative number (`+18005550100`):

```bash
curl -X POST "http://localhost:8000/webhook/sms" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+15551234567&To=+18005550100&Body=How%20do%20I%20get%20help%3F"
```

### Response:
```json
{
  "sender": "+15551234567",
  "recipient": "+18005550100",
  "persona": "Warm and Empathetic",
  "reply": "For support requests, please provide your ticket ID and I'd be happy to assist!"
}
```
