# SMS Customer Service Chatbot Backend

A Python FastAPI backend for an SMS customer service chatbot. The system processes incoming SMS webhooks, loads local Markdown documentation as a knowledge base, randomly injects a dynamic personality persona, and generates an LLM response using standard OpenAI SDK.

---

## Features

- **FastAPI Webhook**: Serves a `POST /webhook/sms` endpoint accepting form payloads (`From`, `To`, `Body`).
- **Knowledge Base Loader**: Scans a local `/docs` directory on startup and aggregates all `.md` files into context appended to system instructions.
- **Personality Engine**: Configured with 3 distinct conversational personas ("Warm and Empathetic", "Crisp and Professional", "Witty and Casual") randomly selected for each request.
- **LLM Integration**: Uses standard `openai` SDK to generate concise SMS-suitable responses using system prompt, knowledge base context, and user input.
- **Comprehensive Testing**: Pytest unit tests using FastAPI `TestClient` covering file loading, personality engine, and mocked LLM webhook responses.

---

## Directory Structure

```text
.
├── docs/
│   ├── company_info.md
│   └── faq.md
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

Send an SMS webhook simulation request via `curl`:

```bash
curl -X POST "http://localhost:8000/webhook/sms" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+15551234567&To=+15557654321&Body=What%20is%20your%20return%20policy%3F"
```

### Example Response:

```json
{
  "sender": "+15551234567",
  "recipient": "+15557654321",
  "persona": "Crisp and Professional",
  "reply": "Items can be returned within 30 days of delivery for a full refund."
}
```
